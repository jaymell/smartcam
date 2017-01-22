import abc
import multiprocessing
import cv2
import collections
import datetime

class ImageProcessor(multiprocessing.Process):

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def __init__(self, bg_timeout):
    pass

  @abc.abstractmethod
  def detect_motion(self):
    pass

  @abc.abstractmethod
  def get_frame(self): 
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

  @abc.abstractmethod
  def run(self):
    pass


class CV2ImageProcessor(ImageProcessor):

  def __init__(self, image_queue, bg_timeout):
    self.image_queue = image_queue
    # self.bg_lock = threading.Lock()
    # self.cur_lock = threading.Lock()
    self.bg_timeout = datetime.timedelta(0, bg_timeout)
    self._current = None
    self._background = None
    self._in_motion = False

  def detect_motion(self):
    ## FIXME: temporary
    return False

  def get_frame(self):
    frame = self.image_queue.get()
    return frame

  def background_expired(self):
    return self._current.time - self.bg_timeout >= self._background

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

  def run(self):
    while True:
      frame = self.get_frame()
      self._current = frame
      if self.background_expired():
        self._background = self._current
        self._in_motion = False
        continue
      if not self._in_motion:
        self._in_motion = self.detect_motion()
      if self._in_motion:
        cv2.imshow(t.strftime('%Y-%m-%d'), img)
        cv2.waitKey(int(1000/fps))
