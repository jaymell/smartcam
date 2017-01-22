import abc
import cv2
import logging

logger = logging.getLogger(__name__)

class ImageReader(object):
  """ abstract class for image reader """

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def get_image(self): 
    pass


class CV2ImageReader(ImageReader):

  def __init__(self, video_source):
    try:
      self._cam = cv2.VideoCapture(video_source)
    except Exception as e:
      logger.critical('Failed to instantiate video capture device: %s' % e)
      raise e

  def get_image(self):
    result, frame = self._cam.read()
    if result is True:
      return frame
    return None
