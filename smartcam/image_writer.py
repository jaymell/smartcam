from smartcam.abstract import ImageWriter
import threading
import queue
import logging
from PIL import Image
import io

logger = logging.getLogger(__name__)

class PILImageWriter(ImageWriter):
  """ write images using PIL """

  def __init__(self, queue, cloud_writer, frame_converter=None):
    threading.Thread.__init__(self)
    self.queue = queue
    self.cloud_writer = cloud_writer
    self.frame_converter = frame_converter
    self.IMAGE_TYPE = 'JPEG'

  def write_image(self, img, name):
    buf = io.BytesIO()
    if self.frame_converter:
      Image.fromarray(self.frame_converter(img)).save(buf, self.IMAGE_TYPE)
    else:
      Image.fromarray(img).save(buf, self.IMAGE_TYPE)
    buf.seek(0)
    if self.cloud_writer:
      logger.debug('writing image to cloud_writer')
      self.cloud_writer.write_fileobj(buf, name)

  def run(self):
    logger.debug("starting PILImagewriter thread")
    while True:
      try:
        frame = self.queue.get()
      except queue.Empty:
        continue
      if frame is None:
        continue
      self.write_image(frame.image, "img/%s" % frame.time)
