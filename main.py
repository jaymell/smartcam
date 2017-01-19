#!/usr/bin/env python3 

import threading
import ConfigParser
import os 
import glob
import logging
import sys
import time
import multiprocessing
import cv2
from frame_reader import FrameThread
from image_reader import CV2ImageReader
from queue_handler import QueueHandler
from image_processor import CV2ImageProcessor

def get_device(use_default=True):
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
  if not use_default:
    dev_nums.pop(0)
  return dev_nums[0]


def get_video_source(config):
  if config['VIDEO_SOURCE'] == 'device':
    return get_device()
  elif config['VIDEO_SOURCE'] == 'device,non-default':
    return get_device(use_default=False)


def detect_motion(image_processor):
  while True:
    # bg = reader.grayscale_image(reader.background)
    # cur = reader.grayscale_image(reader.current)
    img = image_processor.get_image()
    logging.info("Got image")
    # frameDelta = reader.get_delta(bg, cur)
    cv2.imshow('barf', img)
    # cv2.waitKey(100)

def parse_config():
  config_file = "config"
  p = ConfigParser.ConfigParser()
  p.read(config_file)
  
  export = {}
  export['VIDEO_SOURCE'] = os.environ.get('VIDEO_SOURCE', p.get('video', 'source'))
  export['BG_TIMER'] = float(os.environ.get('BG_TIMER', p.get('video', 'bg_timer')))
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
  video_source = get_video_source(config)
  
  video_queue = multiprocessing.Queue()
  image_queue = multiprocessing.Queue()

  try:
    queue_handler = QueueHandler(video_queue, image_queue)
    queue_handler.start()
  except Exception as e:
    logging.critical("Failed to instantiate QueueHandler: %s " % e)
    return 1

  try:
    image_reader = CV2ImageReader(video_source)
  except Exception as e:
    logging.critical("Failed to instantiate CV2ImageReader: %s" % e)
    return 1
  
  try:
    bg_timer = config['BG_TIMER']
    fps = config['FPS']
    frame_reader = FrameThread(image_reader, queue_handler, fps)
    frame_reader.start()
  except Exception as e:
    logging.critical("Failed to instantiate FrameThread: %s" % e)
    return 1

  try: 
    image_processor = CV2ImageProcessor(image_queue)
  except Exception as e:
    logging.critical("Failed to instantiate CV2ImageProcessor: %s" % e)
    return 1

  detect_motion(image_processor)

  sys.exit(0)

if __name__ == '__main__':
  main()