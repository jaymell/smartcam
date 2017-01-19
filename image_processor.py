import abc
# import threading
import cv2

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

  def __init__(self, image_queue):
    self.image_queue = image_queue
    # self.bg_lock = threading.Lock()
    # self.cur_lock = threading.Lock()

    self._current = None
    self._background = None

  def get_image(self):
    frame = self.image_queue.get()
    return frame.image

  def downsample_image(self, image):
    pass 

  def grayscale_image(self, image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

  def get_delta(self, baseline, current):
    return cv2.absdiff(baseline, current)

  @property
  def background(self):
    # with self.bg_lock:
      # logging.debug("locked for background get")
      return self._background

  @background.setter
  def background(self, img):
    # with self.bg_lock:
      # logging.debug("locked for background set")
      self._background = img

  @property
  def current(self):
    # with self.cur_lock:
      # logging.debug("locked for current get")
      return self._current

  @current.setter
  def current(self, img):
    # with self.cur_lock:
      # logging.debug("locked for current set")
      self._current = img
