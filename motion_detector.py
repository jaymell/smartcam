import abc
import cv2
import copy
import datetime
import logging
import multiprocessing
import queue
import video_writer


logger = logging.getLogger(__name__)


def _handle_motion(self, frame):
  logger.debug('motion detected')
  self.last_motion_time = self.current.time
  draw_rectangles(frame.image, contours)
  write_text(frame, frame.time.isoformat())
  video_buffer.append(frame)
  cv2.imshow('MOTION_DETECTED', frame.image)
  # cv2.moveWindow('MOTION_DETECTED', 10, 10)
  cv2.waitKey(1)


def _handle_motion_timeout(self, video_buffer):
  writer = video_writer.CV2VideoWriter(self.video_format,
                                       self.fps,
                                       None,
                                       video_buffer[0].time.isoformat() + '.avi',
                                       video_buffer[0].width,
                                       video_buffer[0].height)
  writer.write(video_buffer)
  video_buffer = []
  self.last_motion_time = None
  cv2.destroyWindow('MOTION_DETECTED')
  # makes destroyWindow work -- may
  # be a better way to do this:
  cv2.waitKey(1)


def resize_image(image, width):
  (h, w) = image.height, image.width
  r = width / float(w)
  dim = (width, int(h * r))
  return cv2.resize(image, dim, interpolation=cv2.INTER_AREA)


def downsample_image(image):
  # image = resize_image(image, 500)
  image = blur_image(image)
  image = grayscale_image(image)
  return image


def grayscale_image(image):
  return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def draw_rectangles(image, contours):
  for c in contours:
    (x, y, w, h) = cv2.boundingRect(c)
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)


def blur_image(image):
  return cv2.GaussianBlur(image, (21, 21), 0)


def find_contours(image, threshold=1200):
    cv2.imshow('findContours', image)
    cv2.waitKey(1)
    thresh = cv2.threshold(image, 50, 255, cv2.THRESH_BINARY)[1]
    (_, _contours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not _contours:
      return None
    contours = []
    [ contours.append(i) for i in _contours if cv2.contourArea(i) > threshold ]
    return contours


def write_text(frame, text):
  (h, w) = frame.height, frame.width
  font = cv2.FONT_HERSHEY_SIMPLEX
  cv2.putText(frame.image, text, (int(w*.05),int(h*.9)), font, .75, (255,255,255), 2, cv2.LINE_AA)


class MotionDetector(multiprocessing.Process):

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def __init__(self, image_queue, bg_timeout, fps, video_format, debug=False):
    pass

  @abc.abstractmethod
  def detect_motion(self):
    pass

  @abc.abstractmethod
  def run(self):
    pass


class CV2BackgroundSubtractorMOG(MotionDetector):
  ''' detect motion using cv2.BackgroundSubtractorMOG
  '''

  def __init__(self, image_queue, motion_timeout, fps, video_format, debug=False):
    multiprocessing.Process.__init__(self)
    self.image_queue = image_queue
    self.cur_lock = multiprocessing.Lock()
    self._current = None
    self.fps = fps
    self.daemon = True
    self.video_format = video_format
    self.debug = debug
    self.fgbg = cv2.bgsegm.createBackgroundSubtractorMOG()

  def get_frame(self):
    frame = self.image_queue.get()
    return frame

  @property
  def current(self):
    with self.cur_lock:
      return self._current

  @current.setter
  def current(self, frame):
    with self.cur_lock:
      self._current = frame
      self._current.image = downsample_image(frame.image)

  def detect_motion(self):
    fgmask = self.fgbg.apply(self.current.image)
    if self.debug:
      cv2.imshow('BackgroundSubtractorMOG', fgmask)
      # cv2.moveWindow('BackgroundSubtractorMOG', 600, 800)
      cv2.waitKey(1)
    contours = find_contours(fgmask)
    return contours

  def run(self):
    logger.debug("starting motion_detector run loop")
    video_buffer = []
    in_motion = False
    while True:
      try:
        frame = self.get_frame()
      except queue.Empty:
        continue
      if frame is None:
        continue
      self.current = copy.deepcopy(frame)
      contours = self.detect_motion()
      if contours is not None:
        draw_rectangles(frame.image, contours)
        write_text(frame, frame.time.isoformat())
        video_buffer.append(frame)
        cv2.imshow('MOTION_DETECTED', frame.image)
        # cv2.moveWindow('MOTION_DETECTED', 10, 10)
        cv2.waitKey(1)


class CV2BackgroundSubtractorGMG(MotionDetector):
  ''' detect motion using cv2.BackgroundSubtractorGMG
  '''

  def __init__(self, image_queue, motion_timeout, fps, video_format, debug=False):
    multiprocessing.Process.__init__(self)
    self.image_queue = image_queue
    self.cur_lock = multiprocessing.Lock()
    self._current = None
    self.fps = fps
    self.daemon = True
    self.video_format = video_format
    self.debug = debug
    self.fgbg = cv2.bgsegm.createBackgroundSubtractorGMG()

  def get_frame(self):
    frame = self.image_queue.get()
    return frame

  @property
  def current(self):
    with self.cur_lock:
      return self._current

  @current.setter
  def current(self, frame):
    with self.cur_lock:
      self._current = frame
      self._current.image = downsample_image(frame.image)

  def detect_motion(self):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
    fgmask = self.fgbg.apply(self.current.image)
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
    if self.debug:
      cv2.imshow('BackgroundSubtractorGMG', fgmask)
      # cv2.moveWindow('BackgroundSubtractorGMG', 200, 200)
      cv2.waitKey(1)
    contours = find_contours(self.current.image)
    return contours

  def run(self):
    logger.debug("starting motion_detector run loop")
    video_buffer = []
    in_motion = False
    while True:
      try:
        frame = self.get_frame()
      except queue.Empty:
        continue
      if frame is None:
        continue
      self.current = copy.deepcopy(frame)
      contours = self.detect_motion()
      if contours is not None:
        draw_rectangles(frame.image, contours)
        write_text(frame, frame.time.isoformat())
        video_buffer.append(frame)
        cv2.imshow('MOTION_DETECTED', frame.image)
        # cv2.moveWindow('MOTION_DETECTED', 10, 10)
        cv2.waitKey(1)


class CV2FrameDiffMotionDetector(MotionDetector):
  ''' detect motion by differencing current and previous
      frame
  '''
  def __init__(self, image_queue, motion_timeout, fps, video_format, debug=False):
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
    self.video_format = video_format
    self.debug = debug

  def detect_motion(self):
    delta = self.get_delta()
    thresh = cv2.threshold(delta, 50, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    (_, _contours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
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

  def get_frame(self):
    frame = self.image_queue.get()
    return frame

  def get_delta(self):
    return cv2.absdiff(self.background.image, self.current.image)

  def background_expired(self):
    return self.current.time - self.bg_timeout >= self.background.time

  @property
  def background(self):
    with self.bg_lock:
      return self._background

  @background.setter
  def background(self, frame):
    with self.bg_lock:
      self._background = frame

  @property
  def current(self):
    with self.cur_lock:
      return self._current

  @current.setter
  def current(self, frame):
    with self.cur_lock:
      if self._current is not None:
        self.background = self._current
      self._current = frame
      self._current.image = downsample_image(frame.image)
      if self.background is None:
        self.background = self._current

  def run(self):
    logger.debug("starting motion_detector run loop")
    video_buffer = []
    in_motion = False
    while True:
      try:
        frame = self.get_frame()
      except queue.Empty:
        continue
      if frame is None:
        continue
      self.current = copy.deepcopy(frame)
      contours = self.detect_motion()
      if contours is not None:

      elif self.motion_is_timed_out():

      ### not currently in motion but still within timeout:
      elif self.last_motion_time != None:
        video_buffer.append(frame)
