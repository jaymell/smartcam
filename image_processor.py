import abc
import multiprocessing
import cv2
import collections
import datetime
import logging

logger = logging.getLogger(__name__)

class ImageProcessor(multiprocessing.Process):

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def __init__(self, image_queue, bg_timeout, fps):
    pass

  @abc.abstractmethod
  def detect_motion(self):
    pass

  @abc.abstractmethod
  def blur_image(self, image):
    pass

  @abc.abstractmethod
  def get_frame(self): 
    pass

  @abc.abstractmethod
  def resize_image(self, image): 
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

  @abc.abstractmethod
  def background_expired(self):
    pass

  @property
  @abc.abstractmethod
  def background(self):
    pass

  @background.setter
  @abc.abstractmethod
  def background(self, image):
    pass

  @property
  @abc.abstractmethod
  def current(self):
    pass

  @current.setter
  @abc.abstractmethod
  def current(self, image):
    pass

  @abc.abstractmethod
  def run(self):
    pass


class CV2ImageProcessor(ImageProcessor):

  def __init__(self, image_queue, bg_timeout, fps):
    self.image_queue = image_queue
    self.bg_lock = multiprocessing.Lock()
    self.cur_lock = multiprocessing.Lock()
    self.bg_timeout = datetime.timedelta(0, bg_timeout)
    self._current = None
    self._background = None
    self._in_motion = False
    self.fps = fps
    multiprocessing.Process.__init__(self)

  def detect_motion(self):
    delta = self.get_delta()
    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts:
      if cv2.contourArea(c) < args["min_area"]:
        return False
    return True

  def blur_image(self, image):
    return cv2.GaussianBlur(image, (21, 21), 0)

  def get_frame(self):
    frame = self.image_queue.get()
    return frame

  def resize_image(self, image, width):
    (h, w) = image.shape[:2]
    logger.debug('dimensions: %s, %s' % (h, w))
    r = width / float(w)
    dim = (width, int(h * r))
    return cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

  def downsample_image(self, image):
    image = self.resize_image(image, 500)
    image = self.grayscale_image(image)
    image = self.blur_image(image)
    return image

  def grayscale_image(self, image):
    logger.debug('this is my image: %s' % image)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

  def get_delta(self):
    return cv2.absdiff(self.background.image, self.current.image)

  def background_expired(self):
    return self.current.time - self.bg_timeout >= self.background.time

  @property
  def background(self):
    with self.bg_lock:
      logging.debug("locked for background get")
      return self._background

  @background.setter
  def background(self, frame):
    with self.bg_lock:
      logging.debug("locked for background set")
      self._background = frame
      self._background.image = self.downsample_image(frame.image)

  @property
  def current(self):
    with self.cur_lock:
      logging.debug("locked for current get")
      return self._current

  @current.setter
  def current(self, frame):
    with self.cur_lock:
      logging.debug("locked for current set")
      self._current = frame
      self._current.image = self.downsample_image(frame.image)

  def run(self):
    logging.debug("starting image_processor thread")
    while True:
      logging.debug("getting frame")
      frame = self.get_frame()
      logging.debug("got frame")
      self.current = frame
      if self.background == None or self.background_expired():
        logging.debug("setting background")
        self.background = self.current
        self._in_motion = False
        continue
      if not self._in_motion:
        logging.debug("detecting motion")
        self._in_motion = self.detect_motion()
      if self._in_motion:
        logging.debug('motion detected')
        cv2.imshow('MOTION_DETECTED', frame.image)
        cv2.waitKey(int(1000/self.fps))
