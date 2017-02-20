import abc
import multiprocessing


class CloudWriter(metaclass=abc.ABCMeta):
  """ abstract interface for video writers """  
  
  @abc.abstractmethod
  def write(self):
  	pass


class MotionDetectorProcess(multiprocessing.Process, metaclass=abc.ABCMeta):
  ''' abstract class for handling motion detection thread loop '''

  @abc.abstractmethod
  def __init__(self, 
               motion_detector, 
               image_queue, 
               motion_timeout, 
               video_writer):
    pass

  @abc.abstractmethod
  def get_frame(self):
    pass

  @abc.abstractmethod
  def run(self):
    pass


class MotionDetector(multiprocessing.Process, metaclass=abc.ABCMeta):
  ''' interface for motion detectors '''

  @abc.abstractmethod
  def __init__(self, debug=False):
    pass

  @abc.abstractmethod
  def detect_motion(self):
    pass


class FrameReader(metaclass=abc.ABCMeta):
  """ abstract class for image reader """

  @abc.abstractmethod
  def get_frame(self): 
    pass


class VideoProcessor(metaclass=abc.ABCMeta):

  @abc.abstractmethod
  def get_frame(self): 
    pass


class VideoWriter(metaclass=abc.ABCMeta):
  """ abstract class for writing videos """

  @abc.abstractmethod
  def __init__(self, fmt, fps, path=None, s3_writer=None):
    pass

  @abc.abstractmethod
  def write(self, frames, file_name=None, ext='avi', is_color=True):
    """ frames should be array of Frame objects """
    pass

