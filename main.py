#!/usr/bin/env python

import threading
import configparser
import os 
import glob
import logging
import sys
import multiprocessing
import cv2
import time
from frame_reader import CV2FrameReader, run_frame_thread
from queue_handler import QueueHandler
from motion_detector import CV2FrameDiffMotionDetector
from video_processor import CV2VideoProcessor

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
  export['VIDEO_SOURCE'] = os.environ.get('VIDEO_SOURCE', p.get('video', 'source'))
  export['MOTION_TIMEOUT'] = float(os.environ.get('MOTION_TIMEOUT', p.get('video', 'motion_timeout')))
  export['VIDEO_FORMAT'] = os.environ.get('VIDEO_FORMAT', p.get('video', 'video_format'))
  export['FPS'] = float(os.environ.get('FPS', p.get('video', 'fps')))
  return export


def main():
  """ process for initialization:
      1) initialize video source and reader class
      2) initialize VideoProcessor
      3) initialize ImageProcessor
      4) initialize QueueHandler with queues from obj's in 2 and 3
      5) initalize FrameReader with queue from 4 
  """

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
    frame_thread = multiprocessing.Process(target=run_frame_thread, args=(frame_reader, queue_handler, fps))
    frame_thread.start()
  except Exception as e:
    logger.critical("Failed to start frame_thread: %s" % e)
    return 1

  try:
    logger.debug('starting motion_detector')
    motion_detector = CV2FrameDiffMotionDetector(image_queue, motion_timeout, fps, video_format)
    motion_detector.start()
  except Exception as e:
    logger.critical("Failed to instantiate CV2FrameDiffMotionDetector: %s" % e)
    return 1

  try: 
    video_processor = CV2VideoProcessor(video_queue)
  except Exception as e:
    logger.critical("Failed to instantiate CV2ImageProcessor: %s" % e)
    return 1

  show_video(video_processor, fps)
  frame_thread.join(); motion_detector.join(); queue_hander.join()
  sys.exit(0)

if __name__ == '__main__':
  main()
