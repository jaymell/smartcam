import abc
import cv2
import logging
import datetime
import threading
import time

class Frame:
  def __init__(self, image):
    self.image = image
    self.time = datetime.datetime.now()


class FrameThread(threading.Thread):
  """ thread for setting background image;
      initialized with ImageProcessor obj and
      desired time to delay background being set, 
      in seconds """
  
  def __init__(self, image_reader, queue_handler, fps):
    self.fps = fps
    self.image_reader = image_reader
    self.queue_handler = queue_handler
    threading.Thread.__init__(self)

  def run(self):
    while True:
      logging.info("getting new frame")
      try:
        frame = Frame(self.image_reader.get_image())
      except Exception as e:
        logging.error("Failed to instantiate Frame: %s" % e)
      try:
        self.queue_handler.put(frame)
      except Exception as e:
        print("Failed to put frame onto queue: %s" % e)
      time.sleep(1.0/self.fps)
