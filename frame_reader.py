import abc
import cv2
import logging
import datetime
import Queue
import multiprocessing
import time


logger = logging.getLogger(__name__)


class Frame:
  def __init__(self, image):
    self.image = image
    self.time = datetime.datetime.now()

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


class FrameReader(multiprocessing.Process):
  """ thread for setting background image;
      initialized with ImageProcessor obj and
      desired time to delay background being set, 
      in seconds """
  
  def __init__(self, image_reader, queue_handler, fps):
    multiprocessing.Process.__init__(self)
    self.fps = fps
    self.image_reader = image_reader
    self.queue_handler = queue_handler
    self.daemon = True

  def run(self):
    logging.debug("starting frame_reader run loop")
    while True:
      logger.debug("getting new frame")
      try:
        frame = Frame(self.image_reader.get_image())
      except Queue.Empty:
        # SHOULD I PAUSE HERE?
        continue
      except Exception as e:
        logger.error("Failed to instantiate Frame: %s" % e)
      try:
        self.queue_handler.put(frame)
      except Exception as e:
        print("Failed to put frame onto queue: %s" % e)
      time.sleep(1.0/self.fps)
