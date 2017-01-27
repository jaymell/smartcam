import abc
import ConfigParser
import cv2
import glob
import logging
import os
import sys
import time
import threading

IN_MOTION = False


class FrameThread(threading.Thread):
  """ thread for setting background image;
      initialized with ImageProcessor obj and
      desired time to delay background being set, 
      in seconds """
  
  def __init__(self, image_processor, bg_timer, fps):
    self.image_processor = image_processor
    self.bg_timer = bg_timer
    # set to get background immediately:
    self.bg_timeout = time.time() - self.bg_timer
    self.fps = fps
    threading.Thread.__init__(self)

  def background_expired(self):
    """ return true/false if time expired """
    return time.time() - self.bg_timeout >= self.bg_timer

  def run(self):
    timeout = time.time()
    while True:
      logging.info("getting new frame")
      if (not IN_MOTION) and self.background_expired():
        self.image_processor.background = self.image_processor.current = self.image_processor.get_image()
        self.bg_timeout = time.time()
      else:
        self.image_processor.current = self.image_processor.get_image()
      time.sleep(1.0/self.fps)


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

  @property
  @abc.abstractmethod
  def current(self):
    pass

  @current.setter
  @abc.abstractmethod
  def current(self, img):
    pass


class CV2ImageProcessor(ImageProcessor):

  def __init__(self, video_source):
    try:
      self.cam = cv2.VideoCapture(video_source)
    except Exception as e:
      logging.critical('Failed to instantiate video capture device: %s' % e)
      raise e

    self.bg_lock = threading.Lock()
    self.cur_lock = threading.Lock()

    self._current = None
    self._background = None

  def get_image(self):
    result, frame = self.cam.read()
    if result is True:
      print("frame: ", frame)
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
    with self.bg_lock:
      logging.debug("locked for background get")
      return self._background

  @background.setter
  def background(self, img):
    with self.bg_lock:
      logging.debug("locked for background set")
      self._background = img

  @property
  def current(self):
    with self.cur_lock:
      logging.debug("locked for current get")
      return self._current

  @current.setter
  def current(self, img):
    with self.cur_lock:
      logging.debug("locked for current set")
      self._current = img
   

def parse_config():
  config_file = "config"
  p = ConfigParser.ConfigParser()
  p.read(config_file)
  
  export = {}
  export['VIDEO_SOURCE'] = os.environ.get('VIDEO_SOURCE', p.get('video', 'source'))
  export['BG_TIMER'] = float(os.environ.get('BG_TIMER', p.get('video', 'bg_timer')))
  export['FPS'] = float(os.environ.get('FPS', p.get('video', 'fps')))
  return export


def get_device(use_default=False):
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


def detect_motion(reader):
  while True:
    bg = reader.grayscale_image(reader.background)
    cur = reader.grayscale_image(reader.current)
    logging.info("Got image")
    frameDelta = reader.get_delta(bg, cur)
    cv2.imshow('barf', frameDelta)
    cv2.waitKey(100)


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
    bg_timer = config['BG_TIMER']
    fps = config['FPS']
    FrameThread(reader, bg_timer, fps).start()
  except Exception as e:
    logging.critical("Failed to instantiate FrameThread: %s" % e)
    return 1

  # is there a more elegant way to avoid race condition
  # between background setting and loop below?
  while reader.background is None:
    print('where am i')
    time.sleep(.1)

  detect_motion(reader)

  sys.exit(0)

if __name__ == '__main__': 
  logging.basicConfig(level=logging.DEBUG)
  rc = main()
  sys.exit(rc)

