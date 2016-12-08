import abc
import ConfigParser
import cv2
import glob
import logging
import os
import sys
import time
import threading


class BGThread(threading.Thread):
  """ thread for setting background image;
      initialized with ImageProcessor obj and
      desired time to delay background being set, 
      in seconds """
  
  def __init__(self, image_processor, bg_time=2):
    self.image_processor = image_processor
    self.bg_time = bg_time
    image_processor.lock = threading.Lock()
    threading.Thread.__init__(self)

  def run(self):
    while True:
      logging.info("setting background")
      self.image_processor.background = self.image_processor.get_image()
      time.sleep(self.bg_time)


class ImageProcessor(object):

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
  
  @property
  @abc.abstractmethod
  def background(self):
    pass

  @background.setter
  @abc.abstractmethod
  def background(self, img):
    pass

class CV2ImageProcessor(ImageProcessor):

  def __init__(self, video_source):
    try:
      self.cam = cv2.VideoCapture(video_source)
    except Exception as e:
      logging.critical('Failed to instantiate video capture device: %s' % e)
      raise e
    # this should be set by background thread:
    self.lock = None
    self._background = None

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

  @property
  def background(self):
    with self.lock:
      logging.info("locked for get")
      return self._background

  @background.setter
  def background(self, img):
    logging.info("locked for set")
    with self.lock:
      logging.info("locked for set")
      self._background = img

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
  try:
    BGThread(reader).start()
  except Exception as e:
    logging.critical("Failed to instantiate BGThread: %s" % e)
    return 1

  # is there a more elegant way to avoid race condition
  # between background setting and loop below?
  while reader.background is None:
    time.sleep(.1)

  while True:
    bg = reader.grayscale_image(reader.background)
    cur = reader.grayscale_image(reader.get_image())
    logging.info("Got image")
    frameDelta = reader.get_delta(bg, cur)
    cv2.imshow('barf', frameDelta)
    cv2.waitKey(100)


if __name__ == '__main__': 
  logging.basicConfig(level=logging.DEBUG)
  rc = main()
  sys.exit(rc)

