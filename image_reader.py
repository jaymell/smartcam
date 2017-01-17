import abc
import cv2

class ImageReader:
  """ abstract class for image reader """

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def get_image(self): 
    pass


class CV2ImageReader(ImageProcessor):

  def __init__(self, video_source):
    try:
      self._cam = cv2.VideoCapture(video_source)
    except Exception as e:
      logging.critical('Failed to instantiate video capture device: %s' % e)
      raise e

  def get_image(self):
    result, frame = self._cam.read()
    if result is True:
      print("frame: ", frame)
      return frame
    return None
