import abc
import multiprocessing
import threading

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
  def __init__(self, queue, fps, path=None, cloud_writer=None):
    pass

  @abc.abstractmethod
  def run(self):
    pass


class CloudWriter(metaclass=abc.ABCMeta):
  """ interface for video writers """

  @abc.abstractmethod
  def write_file(self, src, dest):
    pass

  def write_fileobj(self, src, dest):
    """ write to file-like object """
    pass

  def write_str(self, src, dest):
    """ write to file-like object """
    pass


class Queue(metaclass=abc.ABCMeta):
  """ queue interface """

  @abc.abstractmethod
  def get(self):
    pass

  def put(self, item):
    pass
