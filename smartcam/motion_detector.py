import cv2
import copy
import datetime
import logging
import multiprocessing
import numpy as np
import queue
import threading
from smartcam.abstract import MotionDetectorProcess, MotionDetector


logger = logging.getLogger(__name__)


def equalize_image(image):
  ''' currently using to improve contrast of low-light images --
      see this page:
      docs.opencv.org/3.2.0/d5/daf/tutorial_py_histogram_equalization.html
  '''

  # hist, bins = np.histogram(image.flatten(), 256,[0,256])
  # cdf = hist.cumsum()
  # cdf_normalized = cdf * hist.max() / cdf.max()
  # cdf_m = np.ma.masked_equal(cdf,0)
  # cdf_m = (cdf_m - cdf_m.min())*255/(cdf_m.max()-cdf_m.min())
  # cdf = np.ma.filled(cdf_m,0).astype('uint8')
  # return cdf[image]
  return cv2.equalizeHist(image)


def resize_image(image, width):
  (h, w) = img.shape[:2]
  r = width / float(w)
  dim = (width, int(h * r))
  return cv2.resize(image, dim, interpolation=cv2.INTER_AREA)


def downsample_image(image):
  image = resize_image(image, 400)
  image = blur_image(image)
  image = grayscale_image(image)
  # image = cv2.Canny(image, 30, 200)
  return image


def grayscale_image(image):
  return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def adaptive_threshold_image(image):
  return cv2.adaptiveThreshold(image,
                               255,
                               cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY,
                               11,
                               2)


def threshold_image(image, threshold=25):
  return cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)[1]


def draw_rectangles(image, contours):
  for c in contours:
    (x, y, w, h) = cv2.boundingRect(c)
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 1)


def draw_contours(image, contours):
  cv2.drawContours(image, contours, -1, (0, 0, 255), 1)


def blur_image(image):
  return cv2.GaussianBlur(image, (21, 21), 0)


def find_contours(image, threshold=100, debug=False):
    t0 = datetime.datetime.now()
    (_, _contours, _) = cv2.findContours(image, cv2.RETR_TREE,
      cv2.CHAIN_APPROX_SIMPLE)
    t1 = datetime.datetime.now()
    if not _contours:
      return None
    contours = [ i for i in _contours if cv2.contourArea(i) > threshold ]
    t2 = datetime.datetime.now()
    if debug:
      logger.debug("findContours time: %s" % ((t1-t0).total_seconds()))
      logger.debug("filter contours time: %s" % ((t2-t1).total_seconds()))
    return contours


def write_text(frame, text):
  (h, w) = frame.height, frame.width
  font = cv2.FONT_HERSHEY_SIMPLEX
  cv2.putText(frame.image, text, (int(w*.05),int(h*.9)), font, .75,
    (255,255,255), 2, cv2.LINE_AA)


class CV2MotionDetectorProcess(MotionDetectorProcess):

  def __init__(self,
               motion_detector,
               image_queue,
               motion_queue,
               motion_timeout,
               debug=False,
               show_video=False):
    multiprocessing.Process.__init__(self)
    self.name = CV2MotionDetectorProcess.__name__
    self.motion_detector = motion_detector
    self.image_queue = image_queue
    self.motion_timeout = datetime.timedelta(0, motion_timeout)
    self.motion_queue = motion_queue
    self.last_motion_time = None
    self.frame = None
    self.debug = debug
    self.show_video = show_video

  def handle_motion(self, contours):
    logger.debug('motion detected')
    self.last_motion_time = self.frame.time
    # draw_rectangles(self.frame.image, contours)
    # draw_contours(self.frame.image, contours)
    self.motion_queue.put(self.frame)
    if self.show_video:
      cv2.imshow('MOTION_DETECTED', self.frame.image)
      cv2.waitKey(1)

  def handle_motion_timeout(self):
    buf = []
    self.last_motion_time = None
    if self.show_video:
      cv2.destroyWindow('MOTION_DETECTED')
      # makes destroyWindow work -- may
      # be a better way to do this:
      cv2.waitKey(1)
    self.motion_queue.put(None)

  def motion_is_timed_out(self):
    ''' return true/false -- has it been longer than self.motion_timeout
        since motion was detected? '''
    if self.last_motion_time is None:
      return False
    return self.frame.time - self.last_motion_time >= self.motion_timeout

  def get_frame(self):
    frame = self.image_queue.get()
    return frame

  def run(self):
    logger.debug("starting motion_detector thread loop")
    video_buffer = []
    in_motion = False
    while True:
      try:
        self.frame = self.get_frame()
      except queue.Empty:
        continue
      if self.frame is None:
        continue
      self.motion_detector.current = copy.deepcopy(self.frame)
      write_text(self.frame, self.frame.time.isoformat())
      contours = self.motion_detector.detect_motion()
      if contours:
        self.handle_motion(contours)
      elif self.motion_is_timed_out():
        self.handle_motion_timeout()
      ### not currently in motion but still within timeout period:
      elif self.last_motion_time != None:
        self.motion_queue.put(self.frame)


class CV2BackgroundSubtractorMOG(MotionDetector):
  ''' detect motion using cv2.BackgroundSubtractorMOG
  '''

  def __init__(self, debug=False, show_video=False):
    self.cur_lock = multiprocessing.Lock()
    self._current = None
    self.daemon = True
    self.debug = debug
    self.show_video = show_video
    self.fgbg = cv2.bgsegm.createBackgroundSubtractorMOG()

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
    fgmask = adaptive_threshold_image(self.current.image)
    fgmask = self.fgbg.apply(fgmask)
    if self.show_video:
      cv2.imshow('BackgroundSubtractorMOG', fgmask)
      cv2.waitKey(1)
    contours = find_contours(fgmask)
    return contours


class CV2BackgroundSubtractorGMG(MotionDetector):
  ''' detect motion using cv2.BackgroundSubtractorGMG
  '''

  def __init__(self, debug=False, show_video=False):
    self.cur_lock = multiprocessing.Lock()
    self._current = None
    self.daemon = True
    self.debug = debug
    self.show_video = show_video
    self.fgbg = cv2.bgsegm.createBackgroundSubtractorGMG()

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
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
    fgmask = self.fgbg.apply(self.current.image)
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
    thresh = threshold_image(fgmask)
    if self.show_video:
      cv2.imshow('BackgroundSubtractorGMG', thresh)
      cv2.waitKey(1)
    contours = find_contours(thresh)
    return contours


class CV2FrameDiffMotionDetector(MotionDetector):
  ''' detect motion by differencing current and previous
      frame
  '''
  def __init__(self, area_threshold=100, debug=False, show_video=False):
    self.bg_lock = multiprocessing.Lock()
    self.cur_lock = multiprocessing.Lock()
    self._current = None
    self._background = None
    self.daemon = True
    self.debug = debug
    self.show_video = show_video
    self.area_threshold = area_threshold
    self.thresh_times = []
    self.dilate_times = []
    self.contour_times = []
    self.i = 0

  def detect_motion(self):
    self.i = self.i + 1
    delta = self.get_delta()
    if delta is None:
      return None
    if self.show_video:
      cv2.imshow('CV2FrameDiffMotionDetector', delta)
      cv2.waitKey(1)

    t1 = datetime.datetime.now()

    thresh = threshold_image(delta)
    t2 = datetime.datetime.now()

    thresh = cv2.dilate(thresh, None, iterations=2)
    t3 = datetime.datetime.now()

    contours = find_contours(thresh, self.area_threshold, debug=self.debug)
    t4 = datetime.datetime.now()

    if self.debug:
      self.thresh_times.append((t2-t1).total_seconds())
      self.dilate_times.append((t3-t2).total_seconds())
      self.contour_times.append((t4-t3).total_seconds())
      if self.i == 20:
        self.i = 0
        logger.debug("Thresh avg. time: %s" % (sum(self.thresh_times)/len(self.thresh_times)))
        logger.debug("Dilate avg. time: %s" % (sum(self.dilate_times)/len(self.dilate_times)))
        logger.debug("Contours avg. time: %s" % (sum(self.contour_times)/len(self.contour_times)))
        self.thresh_times = []
        self.dilate_times = []
        self.contour_times = []
    return contours

  def get_delta(self):
    if self.background is None or self.current is None:
      return None
    return cv2.absdiff(self.background.image, self.current.image)

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

