import abc
import queue
import multiprocessing
import cv2
import logging


logger = logging.getLogger(__name__)


class VideoProcessor(object):

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def get_frame(self): 
    pass

class CV2VideoProcessor(VideoProcessor):

  def __init__(self, video_queue):
    self.video_queue = video_queue

  def get_frame(self):
    frame = self.video_queue.get()
    return frame
