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

  def __init__(self, fmt, fps, path, file_name, ext, width, height, is_color=True):
    self.fmt = fmt.upper()
    self.fps = fps
    if path is not None:
      self.path = path
    else:
      self.path = os.path.join(os.path.expanduser('~'), 'Videos')
    self.file_name = file_name
    if ext is None:
      _ext = 'avi'
    else:
       _ext = ext
    self.file_name = self.file_name + '.' + _ext
    self.full_path = os.path.join(self.path, self.file_name)
    self.width = width
    self.height = height
    self.is_color = is_color
    try:
      self.writer = cv2.VideoWriter(self.full_path,
                                    cv2.VideoWriter_fourcc(*self.fmt), 
                                    self.fps, 
                                    (self.width,self.height), 
                                    self.is_color)
    except Exception as e:
      logger.debug('Failed to instantiate cv2.VideoWriter')
      raise e

  def write(self, frames):
    logger.debug('Writing video')
    [ self.writer.write(i.image) for i in frames ]
