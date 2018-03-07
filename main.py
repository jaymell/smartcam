#!/usr/bin/env python3

import threading
import configparser
import os
import glob
import logging
import sys
import multiprocessing
import cv2
import time
import argparse
import smartcam
from smartcam.cloud.aws import S3Writer, KinesisWriter
from smartcam.frame_reader import CV2FrameReader, run_frame_thread
from smartcam.queue_tee import QueueTee
from smartcam.motion_detector import ( CV2MotionDetectorProcess,
                              CV2FrameDiffMotionDetector,
                              CV2BackgroundSubtractorMOG,
                              CV2BackgroundSubtractorGMG )
from smartcam.video_processor import CV2VideoProcessor
from smartcam.video_writer import VideoWriterImpl
from smartcam.frame_writer import FrameWriter
from smartcam.api_manager import APIManager
from smartcam.queue import Queue

logger = logging.getLogger(__name__)


def get_device(use_default=True, device_path=None):
  """ assume lowest index camera found
      is the default -- if use_default False,
      return second-lowest camera index
      FIXME: this doesn't work very well!!! """
  devs = glob.glob('/sys/class/video4linux/*')
  dev_nums = []
  for dev in devs:
    with open(os.path.join(dev, 'dev')) as f:
      dev_num = f.read().rstrip()
      dev_nums.append(int(dev_num.split(':')[1]))
  dev_nums.sort()
  logger.debug('dev_nums: %s' % dev_nums)
  if not use_default:
    dev_nums.pop(0)
  return dev_nums[0]


def get_video_source(config):
  try:
    dev_num = int(config['VIDEO_SOURCE'])
    return dev_num
  except ValueError:
    pass
  if config['VIDEO_SOURCE'] == 'device':
    return get_device()
  elif config['VIDEO_SOURCE'] == 'device,non-default':
    return get_device(use_default=False)
  else:
    return config['VIDEO_SOURCE']


def handle_video(video_processor, fps, show_video=False):
  interval = 100.0
  inc = 0
  f1 = None
  while True:
    inc += 1
    frame = video_processor.get_frame()
    if frame is None:
      time.sleep(.1)
      continue
    if inc == interval:
      inc = 0
      if f1 is not None:
        f2 = frame.time
        diff = f2 - f1
        logger.debug("FPS: %s" % (interval/diff.seconds))
      f1 = frame.time
    if show_video:
      img = frame.image
      t = frame.time
      cv2.imshow(t.strftime('%Y-%m-%d'), img)
      cv2.waitKey(1)


def parse_config():
  config_file = "config"
  p = configparser.ConfigParser()
  p.read(config_file)
  export = {}
  export['VIDEO_SOURCE'] = os.environ.get('VIDEO_SOURCE',
    p.get('camera', 'source'))
  export['MOTION_TIMEOUT'] = float(os.environ.get('MOTION_TIMEOUT',
    p.get('camera', 'motion_timeout')))
  export['FPS'] = float(os.environ.get('FPS',
    p.get('camera', 'fps')))
  export['VIDEO_DESTINATION'] = os.environ.get('VIDEO_DESTINATION',
    p.get('storage', 'video_destination'))
  export['IMAGE_DESTINATION'] = os.environ.get('IMAGE_DESTINATION',
    p.get('storage', 'image_destination'))
  export['LOCAL_VIDEO_FOLDER'] = os.environ.get('LOCAL_VIDEO_FOLDER',
    p.get('storage', 'local_video_folder'))
  export['LOCAL_IMAGE_FOLDER'] = os.environ.get('LOCAL_IMAGE_FOLDER',
    p.get('storage', 'local_image_folder'))
  export['S3_BUCKET'] = os.environ.get('S3_BUCKET',
    p.get('storage', 's3_bucket'))
  export['AWS_REGION'] = os.environ.get('AWS_REGION',
    p.get('storage', 'aws_region'))
  export['KINESIS_STREAM'] = os.environ.get('KINESIS_STREAM',
    p.get('storage', 'kinesis_stream'))
  export['CAMERA_ID'] = os.environ.get('CAMERA_ID',
    p.get('camera', 'camera_id'))
  export['BASE_API_URL'] = os.environ.get('BASE_API_URL',
    p.get('api', 'base_url'))
  export['MOTION_AREA_THRESH'] = int(os.environ.get('MOTION_AREA_THRESH',
    p.get('camera', 'motion_area_threshold', fallback=100)))
  return export


def load_api_manager(config):
  url = config['BASE_API_URL']
  return APIManager(url, None)


def load_cloud_video_writer(config, api):
  ''' load object for writing stuff to cloud storage ---
      will return None if not configured '''
  dest = config['VIDEO_DESTINATION']
  if dest == 'local':
    return None
  if dest == 's3':
    return S3Writer(config['AWS_REGION'],
      config['S3_BUCKET'], api, 'video')
  raise ValueError


def load_cloud_frame_writer(config):
  ''' load object for writing stuff to cloud storage ---
      will return None if not configured '''
  dest = config['IMAGE_DESTINATION']
  if dest == 'local':
    return None
  if dest == 's3':
    return S3Writer(config['AWS_REGION'],
      config['S3_BUCKET'], 'img')
  if dest == 'kinesis':
    return KinesisWriter(config['AWS_REGION'],
      config['KINESIS_STREAM'])
  raise ValueError


def load_motion_detector(config):
  pass


def main(show_video=False):
  """ initialize all the things  """

  config = parse_config()
  motion_timeout = config['MOTION_TIMEOUT']
  camera_id = config['CAMERA_ID']
  fps = config['FPS']
  video_source = get_video_source(config)
  frame_queue = Queue("frame_queue", debug=DEBUG)
  video_queue = Queue("video_queue", debug=DEBUG)
  image_queue = Queue("image_queue", debug=DEBUG)
  motion_queue = Queue("motion_queue", debug=DEBUG)
  motion_video_queue = Queue("motion_video_queue", debug=DEBUG)
  motion_image_queue = Queue("motion_image_queue", debug=DEBUG)

  try:
    frame_tee = QueueTee(in_queue=frame_queue,
      out_queues=[video_queue, image_queue],
      name="frame_tee")
    frame_tee.start()
  except Exception as e:
    logger.critical("Failed to load frame_tee: %s " % e)
    return 1

  try:
    motion_tee = QueueTee(in_queue=motion_queue,
     out_queues=[motion_video_queue, motion_image_queue],
     name="motion_tee")
    motion_tee.start()
  except Exception as e:
    logger.critical("Failed to load motion_tee: %s " % e)
    return 1

  try:
    logger.debug('starting frame_reader')
    frame_thread = multiprocessing.Process(target=run_frame_thread,
                                           args=(CV2FrameReader,
                                                 camera_id,
                                                 video_source,
                                                 frame_queue,
                                                 fps))
    frame_thread.start()
  except Exception as e:
    logger.critical("Failed to start frame_thread: %s" % e)
    return 1

  try:
    api_manager = load_api_manager(config)
  except Exception as e:
    logger.critical("Failed to load api_manager: %s" % e)
    return 1

  try:
    cloud_video_writer = load_cloud_video_writer(config, api_manager)
  except Exception as e:
    logger.critical("Failed to load cloud_video_writer: %s" % e)
    return 1

  try:
    cloud_frame_writer = load_cloud_frame_writer(config)
  except Exception as e:
    logger.critical("Failed to load cloud_frame_writer: %s" % e)
    return 1

  try:
    video_writer = VideoWriterImpl(motion_video_queue,
      fps, load_api_manager(config))
    video_writer.start()
  except Exception as e:
    logger.critical("Failed to load video_writer: %s" % e)
    return 1

  try:
    frame_writer = FrameWriter(motion_image_queue, cloud_frame_writer)
    frame_writer.start()
  except Exception as e:
    logger.critical("Failed to load frame_writer: %s" % e)
    return 1

  try:
    # FIXME: make this configurable:
    # motion_detector = CV2BackgroundSubtractorMOG(debug=DEBUG,
    #  show_video=show_video)
    # motion_detector = CV2BackgroundSubtractorGMG(debug=DEBUG,
    #  show_video=show_video)
    motion_detector = CV2FrameDiffMotionDetector(
      area_threshold=config['MOTION_AREA_THRESH'],
      debug=DEBUG,
      show_video=show_video)
  except Exception as e:
    logger.critical("Failed to load motion_detector: %s" % e)
    return 1

  try:
    logger.debug('starting motion_detector process')
    md_process = CV2MotionDetectorProcess(motion_detector,
      image_queue, motion_queue, motion_timeout, debug=DEBUG,
      show_video=show_video)
    md_process.start()
  except Exception as e:
    logger.critical("Failed to load motion_detector process: %s" % e)
    return 1

  try:
    video_processor = CV2VideoProcessor(video_queue)
  except Exception as e:
    logger.critical("Failed to load CV2ImageProcessor: %s" % e)
    return 1

  try:
    api_manager.post_camera(camera_id)
  except Exception as e:
    logger.warn("Failed to post camera: %s" % e)

  handle_video(video_processor, fps, show_video=show_video)

  frame_thread.join()
  md_process.join()
  frame_tee.join()
  motion_tee.join()
  video_writer.join()
  frame_writer.join()

  return 0


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-d', '--debug',
      help="Print lots of debugging statements",
      action="store_const", dest="loglevel", const=logging.DEBUG,
      default=logging.INFO,
  )
  parser.add_argument(
      '-s', '--show-video',
      help="Show live frame stream and motion detection streams",
      action="store_true",
      default=False
  )

  args = parser.parse_args()
  logging.basicConfig(stream=sys.stdout,
    level=args.loglevel,
    format='%(asctime)s %(processName)s %(threadName)s %(message)s')

  global LOG_LEVEL, DEBUG
  LOG_LEVEL = logging.getLogger().level
  DEBUG = LOG_LEVEL == logging.DEBUG
  show_video = args.show_video

  ### reduce aws sdk logging:
  logging.getLogger('boto3').setLevel(logging.WARNING)
  logging.getLogger('botocore').setLevel(logging.WARNING)
  logging.getLogger('nose').setLevel(logging.WARNING)
  logging.getLogger('s3transfer').setLevel(logging.WARNING)

  x = main(show_video)
  sys.exit(x)

