#!/usr/bin/env python3 

from frame_reader import FrameThread
from image_reader import CV2ImageReader


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


def get_video_source(config):
  if config['VIDEO_SOURCE'] == 'device':
    return get_device()
  elif config['VIDEO_SOURCE'] == 'device,non-default':
    return get_device(use_default=False)


def main():
  """ process for initialization:
      1) initialize video source and reader class
      2) initialize VideoProcessor
      3) initialize ImageProcessor
      4) initialize QueueHandler with queues from obj's in 2 and 3
      5) initalize FrameReader with queue from 4 
  """

  config = parse_config()
  video_source = get_video_source(config)
  try:
    reader = CV2ImageReader(video_source)
  except Exception as e:
    logging.critical(e)
    return 1
  logging.info('Instantiated reader')
  try:
    bg_timer = config['BG_TIMER']
    fps = config['FPS']
    FrameThread(reader, bg_timer, fps).start()
  except Exception as e:
    logging.critical("Failed to instantiate FrameThread: %s" % e)
    return 1

  # is there a more elegant way to avoid race condition
  # between background setting and loop below?
  while reader.background is None:
    print('where am i')
    time.sleep(.1)

  detect_motion(reader)

  sys.exit(0)
