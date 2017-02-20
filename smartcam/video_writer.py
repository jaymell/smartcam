import cv2
import logging
import os
from smartcam.abstract import VideoWriter


logger = logging.getLogger(__name__)


class CV2VideoWriter(VideoWriter):
  """ opencv2 video writer """

  def __init__(self, fmt, fps, path=None, cloud_writer=None):
    self.fmt = fmt.upper()
    if path is not None:
      self.path = path
    else:
      self.path = os.path.join(os.path.expanduser('~'), 'Videos')
    if cloud_writer:
      self.cloud_writer = cloud_writer

  def write(self, frames, file_name=None, ext='avi', is_color=True):
    width = frames[0].width
    height = frames[0].height
    if file_name is None:
      file_name = frames[0].time.isoformat()
    file_name = file_name + '.' + ext
    full_path = os.path.join(self.path, file_name)
    try:
      writer = cv2.VideoWriter(full_path,
                               cv2.VideoWriter_fourcc(*fmt), 
                               fps, 
                               (width, height), 
                               is_color)
    except Exception as e:
      logger.debug('Failed to instantiate cv2.VideoWriter')
      raise e
    logger.debug('Writing video to file system')
    [ writer.write(i.image) for i in frames ]
    if self.use_s3:
      self.s3_writer.write(full_path)
