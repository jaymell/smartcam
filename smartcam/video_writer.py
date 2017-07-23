import cv2
import logging
import os
from smartcam.abstract import VideoWriter
import subprocess
from PIL import Image
import numpy

logger = logging.getLogger(__name__)


class CV2VideoWriter(VideoWriter):
  """ opencv2 video writer """

  def __init__(self, fmt, fps, path=None, cloud_writer=None):
    self.fmt = fmt.upper()
    self.fps = fps
    if path is not None:
      self.path = path
    else:
      self.path = os.path.join(os.path.expanduser('~'), 'Videos')
    # may still be None:
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
                               cv2.VideoWriter_fourcc(*self.fmt),
                               self.fps,
                               (width, height),
                               is_color)
    except Exception as e:
      logger.debug('Failed to write video')
      raise e
    logger.debug('Writing video to file system')
    [ writer.write(i.image) for i in frames ]
    # if self.cloud_writer is not None:
    #   self.cloud_writer.write(full_path)


class FFMpegVideoWriter(VideoWriter):
  """ opencv2 video writer """

  def __init__(self, fmt, fps, path=None, cloud_writer=None):
    self.fmt = fmt.upper()
    self.fps = fps
    if path is not None:
      self.path = path
    else:
      self.path = os.path.join(os.path.expanduser('~'), 'Videos')
    # may still be None:
    self.cloud_writer = cloud_writer

  def write(self, frames, file_name=None, ext='avi', is_color=True):
    width = frames[0].width
    height = frames[0].height
    if file_name is None:
      file_name = frames[0].time.isoformat()
    file_name = file_name + '.' + ext
    full_path = os.path.join(self.path, file_name)
    try:
      p = subprocess.Popen(['ffmpeg', '-y', '-f', 'image2pipe',
        '-s', '%sx%s' % (width, height), '-i', '-',
        '-r', str(self.fps), '-vcodec', 'libx264', '-f', 'mp4', '/tmp/video.mp4'],
                            stdin=subprocess.PIPE)

      [ Image.fromarray(cv2.cvtColor(i.image, cv2.COLOR_RGB2BGR))
          .save(p.stdin, 'JPEG')
            for i in frames ]
      p.stdin.close()
      p.wait()
    except Exception as e:
      logger.debug('Failed to write video')
      raise e
    # logger.debug('Writing video to file system')
    # if self.cloud_writer is not None:
    #   self.cloud_writer.write(full_path)
