import cv2
import logging
import os
from smartcam.abstract import VideoWriter
import subprocess
from PIL import Image
import multiprocessing
import queue

logger = logging.getLogger(__name__)


### NO LONGER MATCHES INTERFACE
# class CV2VideoWriter(VideoWriter):
#   """ opencv2 video writer """

#   def __init__(self, fmt, fps, path=None, cloud_writer=None):
#     self.fmt = fmt.upper()
#     self.fps = fps
#     if path is not None:
#       self.path = path
#     else:
#       self.path = os.path.join(os.path.expanduser('~'), 'Videos')
#     # may still be None:
#     self.cloud_writer = cloud_writer

#   def write(self, frames, file_name=None, ext='avi', is_color=True):
#     width = frames[0].width
#     height = frames[0].height
#     if file_name is None:
#       file_name = frames[0].time.isoformat()
#     file_name = file_name + '.' + ext
#     full_path = os.path.join(self.path, file_name)
#     try:
#       writer = cv2.VideoWriter(full_path,
#                                cv2.VideoWriter_fourcc(*self.fmt),
#                                self.fps,
#                                (width, height),
#                                is_color)
#     except Exception as e:
#       logger.debug('Failed to write video')
#       raise e
#     logger.debug('Writing video to file system')
#     [ writer.write(i.image) for i in frames ]
#     # if self.cloud_writer is not None:
#     #   self.cloud_writer.write(full_path)


class FfmpegVideoWriter(VideoWriter):
  """ opencv2 video writer """

  def __init__(self, queue, fmt, fps, path=None, cloud_writer=None):
    multiprocessing.Process.__init__(self)
    self.queue = queue
    self.fmt = fmt.upper()
    self.fps = fps
    if path is not None:
      self.path = path
    else:
      self.path = os.path.join(os.path.expanduser('~'), 'Videos')
    # may still be None:
    self.cloud_writer = cloud_writer

  def get_writer(self, width, height, file_prefix, ext='avi', is_color=True):
    logger.debug("called get_writer")
    file_name = file_prefix + '.' + ext
    full_path = os.path.join(self.path, file_name)
    p = subprocess.Popen(['ffmpeg', '-y', '-f', 'image2pipe',
      '-s', '%sx%s' % (width, height), '-i', '-',
      '-r', str(self.fps), '-vcodec', 'libx264', '-f', 'mp4', full_path ],
       stdin=subprocess.PIPE)

    def writer(frame):
      logger.debug("writing frame")
      if frame is None:
        logger.debug("closing write process")
        p.stdin.close()
        p.wait()
        return
    # if self.cloud_writer is not None:
    #   self.cloud_writer.write(full_path)
      Image.fromarray(cv2.cvtColor(frame.image,
        cv2.COLOR_RGB2BGR)).save(p.stdin, 'JPEG')

    return writer

  def run(self):
    writer = None
    while True:
      try:
        frame = self.queue.get()
      except queue.Empty:
        continue
      if frame is None:
        if writer is not None:
          writer(frame)
          writer = None
        continue
      if writer is None:
        writer = self.get_writer(frame.width, frame.height,
          frame.time.isoformat(), ext='mp4')
      writer(frame)
