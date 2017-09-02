import threading
import queue
import logging
from PIL import Image

logger = logging.getLogger(__name__)

class FrameWriter(threading.Thread):
  """ write images using PIL """

  def __init__(self, queue, cloud_writer):
    threading.Thread.__init__(self)
    self.queue = queue
    self.cloud_writer = cloud_writer

  def write_frame(self, frame):
    self.cloud_writer.write_str(frame.serialize(), "img/%s" % frame.time)

  def run(self):
    logger.debug("starting FramePickler thread")
    while True:
      try:
        frame = self.queue.get()
      except queue.Empty:
        continue
      if frame is None:
        continue
      self.write_frame(frame)
