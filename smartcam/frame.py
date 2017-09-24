import datetime
import cv2
from PIL import Image
import io
import json
import base64


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
