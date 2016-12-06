import cv2
import abc
import glob
import os

def get_device(use_default=True):
  """ assume lowest index camera found
       is the default -- if use_default False,
       return second-lowest camera index """
  devs = glob.glob('/sys/class/video4linux/*')
  dev_nums = []
  for dev in devs:
    with open(os.path.join(dev, 'dev')) as f:
      dev_num = f.read().rstrip()
      dev_nums.append(int(dev_num.split(':')[1]))
  dev_nums.sort()
  if not use_default:
    dev_nums.pop(0)
  return dev_nums[0]


class VideoSource:
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def get_image(self): 
    pass


class DeviceVideo(VideoSource):

  def __init__(self, camidx):
    # need a clean way to be able to find non-default
    # camera
    self.camidx = camidx

  def get_image():
    pass
