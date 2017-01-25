import abc
import cv2
import logging
import os

logger = logging.getLogger(__name__)


class VideoWriter(object):
  """ abstract class for writing videos """

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def __init__(self, fmt, fps, path, file_name, width, height, is_color=True):
    pass

  @abc.abstractmethod
  def write(self, frames):
    """ frames should be array of Frame objects """
    pass


class CV2VideoWriter(VideoWriter):
  """ opencv2 video writer """

  def __init__(self, fmt, fps, path, file_name, width, height, is_color=True):
    self.fmt = fmt.upper()
    self.fps = fps
    self.path = path
    self.file_name = file_name 
    self.full_path = os.path.join(self.path, self.file_name)
    self.width = width
    self.height = height
    self.is_color = is_color
    try:
      self.writer = cv2.VideoWriter(self.full_path,
                                    cv2.cv.CV_FOURCC(*self.fmt), 
                                    self.fps, 
                                    (self.width,self.height), 
                                    self.is_color)
    except Exception as e:
      logger.debug('Failed to instantiate cv2.VideoWriter')
      raise e

  def write(self, frames):
    [ self.writer.write(i.image) for i in frames ]
