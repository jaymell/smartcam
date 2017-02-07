import abc
import cv2
import copy
import datetime
import logging
import multiprocessing
import Queue
import video_writer

logger = logging.getLogger(__name__)


class MotionDetector(multiprocessing.Process):

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def __init__(self, image_queue, bg_timeout, fps):
    pass

  @abc.abstractmethod
  def detect_motion(self):
    pass

  @abc.abstractmethod
  def run(self):
    pass


class CV2FrameDiffMotionDetector(MotionDetector):

  def __init__(self, image_queue, motion_timeout, fps, video_format):
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
    (h, w) = image.height, image.width
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

  def write_text(self, frame, text):
    (h, w) = frame.height, frame.width
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame.image, text, (int(w*.05),int(h*.9)), font, .75, (255,255,255), 2, cv2.CV_AA)

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
        self.write_text(frame, frame.time.isoformat())
        video_buffer.append(frame)
        cv2.imshow('MOTION_DETECTED', frame.image)
        cv2.moveWindow('MOTION_DETECTED', 10, 10)
        cv2.waitKey(1)
      elif self.motion_is_timed_out():
        writer = video_writer.CV2VideoWriter(self.video_format,
                                             self.fps,
                                             '/home/james/Videos',
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