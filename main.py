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
import smartcam
from smartcam.frame_reader import CV2FrameReader, run_frame_thread
from smartcam.queue_handler import QueueHandler
from smartcam.motion_detector import ( CV2MotionDetectorProcess,
                              CV2FrameDiffMotionDetector,
                              CV2BackgroundSubtractorMOG,
                              CV2BackgroundSubtractorGMG )
from smartcam.video_processor import CV2VideoProcessor
from smartcam.video_writer import CV2VideoWriter

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_device(use_default=True, device_path=None):
  """ assume lowest index camera found
       is the default -- if use_default False,
       return second-lowest camera index """

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


def show_video(video_processor, fps):
  while True:
    frame = video_processor.get_frame()
    if frame is None:
      time.sleep(.1)
      continue
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
    p.get('video', 'source'))
  export['MOTION_TIMEOUT'] = float(os.environ.get('MOTION_TIMEOUT',
    p.get('video', 'motion_timeout')))
  export['VIDEO_FORMAT'] = os.environ.get('VIDEO_FORMAT',
    p.get('video', 'video_format'))
  export['FPS'] = float(os.environ.get('FPS',
    p.get('video', 'fps')))
  export['DESTINATION'] = os.environ.get('DESTINATION',
    p.get('storage', 'destination'))
  export['LOCAL_FOLDER'] = os.environ.get('LOCAL_FOLDER',
    p.get('storage', 'local_folder'))
  export['S3_BUCKET'] = os.environ.get('S3_BUCKET',
    p.get('storage', 's3_bucket'))
  export['S3_REGION'] = os.environ.get('S3_REGION',
    p.get('storage', 's3_region'))
  return export


def load_cloud_writer(config):
  ''' load object for writing stuff to cloud storage ---
      will return None if not configured '''
  if config['DESTINATION'] == 's3':
    from smartcam.cloud.aws import S3Writer
    return S3Writer(config['S3_REGION'],
      config['S3_BUCKET'])


def load_motion_detector(config):
  pass


def main():
  """ initialize all the things  """

  config = parse_config()
  motion_timeout = config['MOTION_TIMEOUT']
  fps = config['FPS']
  video_format = config['VIDEO_FORMAT']
  video_source = get_video_source(config)
  video_queue = multiprocessing.Queue()
  image_queue = multiprocessing.Queue()

  try:
    logger.debug('starting queue_handler')
    queue_handler = QueueHandler(video_queue, image_queue, fps)
    queue_handler.start()
  except Exception as e:
    logger.critical("Failed to instantiate QueueHandler: %s " % e)
    return 1

  try:
    frame_reader = CV2FrameReader(video_source)
  except Exception as e:
    logger.critical("Failed to instantiate CV2FrameReader: %s" % e)
    return 1

  try:
    logger.debug('starting frame_reader')
    frame_thread = multiprocessing.Process(target=run_frame_thread,
                                           args=(frame_reader,
                                                 queue_handler,
                                                 fps))
    frame_thread.start()
  except Exception as e:
    logger.critical("Failed to start frame_thread: %s" % e)
    return 1

  try:
    logger.debug('initializing cloud_writer')
    cloud_writer = load_cloud_writer(config)
  except Exception as e:
    logger.critical("Failed to instantiate cloud_writer: %s" % e)
    return 1

  try:
    logger.debug('initializing video_writer')
    video_writer = CV2VideoWriter(video_format, fps, path=None,
      cloud_writer=cloud_writer)
  except Exception as e:
    logger.critical("Failed to instantiate video_writer: %s" % e)
    return 1

  try:
    logger.debug('initializing motion_detector')
    # motion_detector = CV2BackgroundSubtractorMOG(debug=True)
    # motion_detector = CV2BackgroundSubtractorGMG(debug=True)
    motion_detector = CV2FrameDiffMotionDetector(debug=True)
    motion_detector.start()
  except Exception as e:
    logger.critical("Failed to instantiate motion_detector: %s" % e)
    return 1

  try:
    logger.debug('starting motion_detector process')
    md_process = CV2MotionDetectorProcess(motion_detector, image_queue, motion_timeout, video_writer)
    md_process.start()
  except Exception as e:
    logger.critical("Failed to instantiate motion_detector process: %s" % e)
    return 1

  try:
    video_processor = CV2VideoProcessor(video_queue)
  except Exception as e:
    logger.critical("Failed to instantiate CV2ImageProcessor: %s" % e)
    return 1

  show_video(video_processor, fps)
  frame_thread.join(); md_process.join(); queue_handler.join()
  sys.exit(0)

if __name__ == '__main__':
  main()
