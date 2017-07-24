import abc
import multiprocessing


class MotionDetectorProcess(multiprocessing.Process, metaclass=abc.ABCMeta):
  ''' abstract class for handling motion detection thread loop '''

  @abc.abstractmethod
  def __init__(self,
               motion_detector,
               image_queue,
               motion_queue,
               motion_timeout,
               video_writer):
    pass

  @abc.abstractmethod
  def get_frame(self):
    pass

  @abc.abstractmethod
  def run(self):
    pass


class MotionDetector(metaclass=abc.ABCMeta):
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


class VideoWriter(multiprocessing.Process, metaclass=abc.ABCMeta):
  """ abstract class for writing videos """

  @abc.abstractmethod
  def __init__(self, queue, fmt, fps, path=None, cloud_writer=None):
    pass

  @abc.abstractmethod
  def run(self):
    pass


class CloudWriter(metaclass=abc.ABCMeta):
  """ abstract interface for video writers """

  @abc.abstractmethod
  def write(self):
    pass

