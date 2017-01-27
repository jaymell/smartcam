import abc
import Queue
import multiprocessing
import cv2
import collections
import datetime
import logging
import copy
import video_writer

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
  def motion_is_timed_out(self):
    pass

  @abc.abstractmethod
  def draw_rectangles(self):
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

  def __init__(self, image_queue, motion_timeout, fps):
    multiprocessing.Process.__init__(self)
    self.image_queue = image_queue
    self.bg_lock = multiprocessing.Lock()
    self.cur_lock = multiprocessing.Lock()
    self.motion_timeout = datetime.timedelta(0, motion_timeout)
    self._current = None
    self._background = None
    self.fps = fps
    self.daemon = True
    self.last_motion_time = None

  def detect_motion(self):
    delta = self.get_delta()
    thresh = cv2.threshold(delta, 50, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    # cv2.imshow('asdf', thresh)
    # cv2.waitKey(int(1000/self.fps))
    (_contours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not _contours:
      return False, None
    contours = []
    motion_detected = False
    for c in _contours:
      # FIXME: don't hard-code this value
      if cv2.contourArea(c) > 1000:
        motion_detected = True
        contours.append(c)
    return motion_detected, contours

  def motion_is_timed_out(self):
    ''' return true/false -- has it been longer than self.motion_timeout
        since motion was detected? '''
    if self.last_motion_time is None:
      return False
    return self.current.time - self.last_motion_time >= self.motion_timeout

  def draw_rectangles(self, image, contours):
    for c in contours:
      (x, y, w, h) = cv2.boundingRect(c)
      cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)

  def blur_image(self, image):
    return cv2.GaussianBlur(image, (21, 21), 0)

  def get_frame(self):
    frame = self.image_queue.get()
    return frame

  def resize_image(self, image, width):
    (h, w) = image.shape[:2]
    r = width / float(w)
    dim = (width, int(h * r))
    return cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

  def downsample_image(self, image):
    # image = self.resize_image(image, 500)
    image = self.blur_image(image)
    image = self.grayscale_image(image)
    return image

  def grayscale_image(self, image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

  def get_delta(self):
    return cv2.absdiff(self.background.image, self.current.image)

  def background_expired(self):
    return self.current.time - self.bg_timeout >= self.background.time

  def write_text(self, image, text):
    (h, w) = image.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(image, text, (int(w*.05),int(h*.9)), font, .75, (255,255,255), 2, cv2.CV_AA)

  @property
  def background(self):
    with self.bg_lock:
      return self._background

  @background.setter
  def background(self, frame):
    with self.bg_lock:
      # no need to downsample here b/c it's already been done by self.current:
      self._background = frame

  @property
  def current(self):
    with self.cur_lock:
      return self._current

  @current.setter
  def current(self, frame):
    with self.cur_lock:
      self._current = frame
      self._current.image = self.downsample_image(frame.image)

  def run(self):
    logger.debug("starting image_processor run loop")
    video_buffer = []
    in_motion = False
    while True:
      try:
        frame = self.get_frame()
      except Queue.Empty:
        continue
      if self.current:
        self.background = self.current
      self.current = copy.deepcopy(frame)
      if self.background:
        in_motion, contours = self.detect_motion()
      if in_motion:
        logger.debug('motion detected')
        self.last_motion_time = self.current.time
        self.draw_rectangles(frame.image, contours)
        self.write_text(frame.image, frame.time.isoformat())
        video_buffer.append(frame)
        cv2.imshow('MOTION_DETECTED', frame.image)
        cv2.moveWindow('MOTION_DETECTED', 10, 10)
        cv2.waitKey(1)
      elif self.motion_is_timed_out():
        writer = video_writer.CV2VideoWriter('mp42',
                                             self.fps,
                                             '/home/james/Videos',
                                             video_buffer[0].time.isoformat() + '.avi',
                                             w,
                                             h)
        writer.write(video_buffer)
      video_buffer = []
      self.last_motion_time = None
      cv2.destroyWindow('MOTION_DETECTED')
      # makes destroyWindow work -- may
      # be a better way to do this:
      cv2.waitKey(1)





  def old_run(self):
    logger.debug("starting image_processor run loop")
    video_buffer = []
    while True:
      try:
        frame = self.get_frame()
      except Queue.Empty:
        continue
      self.current = copy.deepcopy(frame)
      if self.background == None or self.background_expired():
        (h, w) = frame.image.shape[:2]
        logger.debug("setting background")
        self.background = self.current
        self.in_motion = False
        if video_buffer:
          writer = video_writer.CV2VideoWriter('mp42',
                                               self.fps,
                                               '/home/james/Videos',
                                               video_buffer[0].time.isoformat() + '.avi',
                                               w,
                                               h)
          writer.write(video_buffer)
        video_buffer = []
        cv2.destroyWindow('MOTION_DETECTED')
        # makes destroyWindow work -- may
        # be a better way to do this:
        cv2.waitKey(1)
        continue
      if not self.in_motion:
        self.in_motion = self.detect_motion(frame.image)
      if self.in_motion:
        logger.debug('motion detected')
        self.detect_motion(frame.image)
        self.write_text(frame.image, frame.time.isoformat())
        cv2.imshow('MOTION_DETECTED', frame.image)
        video_buffer.append(frame)
        cv2.moveWindow('MOTION_DETECTED', 0,0)
        cv2.waitKey(1)
