import cv2
import logging
import queue
import multiprocessing
import time
import cv2
from smartcam.frame import Frame
from smartcam.abstract import FrameReader

logger = logging.getLogger(__name__)


class CV2FrameReader(FrameReader):

  def __init__(self, camera_id, video_source):
    self.id = camera_id
    try:
      self._cam = cv2.VideoCapture(video_source)
    except Exception as e:
      logger.critical('Failed to instantiate video capture device: %s' % e)
      raise e

  def get_frame(self):
    result, img = self._cam.read()
    if result is True:
      (h, w) = img.shape[:2]
      return Frame(self.id, img, w, h)

    logger.error('CV2FrameReader read frame error')
    return None


def run_frame_thread(frame_reader, queue, fps):
  logging.debug("starting frame_reader run loop")
  # dump initial frames, as it seems certain cameras
  # flub the first few for some reason:
  for i in range(5):
    frame_reader.get_frame()
  while True:
    try:
      frame = frame_reader.get_frame()
    except queue.Empty:
      continue
    except Exception as e:
      logger.error("Failed to instantiate Frame: %s" % e)
    try:
      queue.put(frame)
    except Exception as e:
      print("Failed to put frame onto queue: %s" % e)
    time.sleep(1.0/fps)
