import abc
import ConfigParser
import cv2
import glob
import logging
import os
import sys
import time


class ImageProcessor:

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def get_image(self): 
    pass

  @abc.abstractmethod
  def downsample_image(self, image):
    pass

  @abc.abstractmethod
  def grayscale_image(self, image):
    pass

  @abc.abstractmethod
  def get_delta(self, baseline, current):
    pass

class CV2ImageProcessor(ImageProcessor):

  def __init__(self, video_source):
    try:
      self.cam = cv2.VideoCapture(video_source)
    except Exception as e:
      logging.critical('Failed to instantiate video capture device: %s' % e)
      raise e 

  def get_image(self):
    result, frame = self.cam.read()
    if result is True:
      return frame
    return None

  def downsample_image(self, image):
    pass 

  def grayscale_image(self, image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

  def get_delta(self, baseline, current):
    return cv2.absdiff(baseline, current)


def parse_config():
  config_file = "config"
  p = ConfigParser.ConfigParser()
  p.read(config_file)
  
  export = {}
  export['VIDEO_SOURCE'] = os.environ.get('VIDEO_SOURCE', p.get('video', 'source'))

  return export


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


def main():
  config = parse_config()
  video_source = get_video_source(config)
  try:
    reader = CV2ImageProcessor(video_source)
  except Exception as e:
    logging.critical(e)
    return 1
  logging.info('Instantiated reader')

  while True: 
    prev = reader.grayscale_image(reader.get_image())
    time.sleep(.1)
    while True:
      cur = reader.grayscale_image(reader.get_image())
      logging.info("Got image")
      frameDelta = reader.get_delta(prev, cur)
      cv2.imshow('barf', frameDelta)
      cv2.waitKey(100)
      time.sleep(5)

if __name__ == '__main__': 
  logging.basicConfig(level=logging.DEBUG)
  rc = main()
  sys.exit(rc)

