import cv2
import logging
import datetime
import queue
import multiprocessing
import time
from smartcam.abstract import FrameReader

logger = logging.getLogger(__name__)


class Frame:
  def __init__(self, image, width, height):
    self.image = image
    self.time = datetime.datetime.now()
    self.width = width
    self.height = height

  @property
  def image(self):
    return self._image

  @image.setter
  def image(self, image):
    self._image = image

  @property
  def time(self):
    return self._time

  @time.setter
  def time(self, time):
    self._time = time


class CV2FrameReader(FrameReader):

  def __init__(self, video_source):
    try:
      self._cam = cv2.VideoCapture(video_source)
    except Exception as e:
      logger.critical('Failed to instantiate video capture device: %s' % e)
      raise e

  def get_frame(self):
    result, img = self._cam.read()
    if result is True:
      (h, w) = img.shape[:2]
      return Frame(img, w, h)

    logger.error('CV2FrameReader read frame error')
    return None


def run_frame_thread(frame_reader, queue_handler, fps):
  logging.debug("starting frame_reader run loop")
  # dump initial frames, as it seems certain cameras
  # flub the first few for some reason:
  for i in range(5):
    frame_reader.get_frame()
  while True:
    try:
      frame = frame_reader.get_frame()
    except queue.Empty:
      # SHOULD I PAUSE HERE?
      continue
    except Exception as e:
      logger.error("Failed to instantiate Frame: %s" % e)
    try:
      queue_handler.put(frame)
    except Exception as e:
      print("Failed to put frame onto queue: %s" % e)
    time.sleep(1.0/fps)
