import cv2
import logging
import datetime
import queue
import multiprocessing
import time
import json
import base64
from smartcam.abstract import FrameReader
import io
from PIL import Image
import cv2

logger = logging.getLogger(__name__)


class Frame:
  def __init__(self, camera_id, image, width, height):
    self.id = camera_id
    self.image = image
    self.time = datetime.datetime.utcnow()
    self.width = width
    self.height = height
    self.image_type = 'JPEG'

  @property
  def image(self):
    return self._image

  @image.setter
  def image(self, image):
    self._image = image

  @property
  def time(self):
    return self._time

  @time.setter
  def time(self, time):
    self._time = time

  def frame_converter(self, x):
    return cv2.cvtColor(x, cv2.COLOR_RGB2BGR)

  def encode(self):
    buf = io.BytesIO()
    if self.frame_converter:
      Image.fromarray(self.frame_converter(self.image)).save(buf, self.image_type)
    else:
      Image.fromarray(self.image).save(buf, self.image_type)
    return buf

  def encode_str(self):
    ''' convert encoded buffer to byte string '''
    return self.encode().getvalue()

  def serialize(self):
    return json.dumps({
      'id': self.id,
      'time': self.time.__str__(),
      'width': self.width,
      'height': self.height,
      'image': base64.b64encode(self.encode_str()).decode('utf-8')
    })


class CV2FrameReader(FrameReader):

  def __init__(self, camera_id, video_source):
    self.id = camera_id
    try:
      self._cam = cv2.VideoCapture(video_source)
    except Exception as e:
      logger.critical('Failed to instantiate video capture device: %s' % e)
      raise e

  def get_frame(self):
    result, img = self._cam.read()
    if result is True:
      (h, w) = img.shape[:2]
      return Frame(self.id, img, w, h)

    logger.error('CV2FrameReader read frame error')
    return None


def run_frame_thread(frame_reader, queue, fps):
  logging.debug("starting frame_reader run loop")
  # dump initial frames, as it seems certain cameras
  # flub the first few for some reason:
  for i in range(5):
    frame_reader.get_frame()
  while True:
    try:
      frame = frame_reader.get_frame()
    except queue.Empty:
      continue
    except Exception as e:
      logger.error("Failed to instantiate Frame: %s" % e)
    try:
      queue.put(frame)
    except Exception as e:
      print("Failed to put frame onto queue: %s" % e)
    time.sleep(1.0/fps)
