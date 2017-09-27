import cv2
import logging
import os
import subprocess
from PIL import Image
import multiprocessing
import queue
from smartcam.abstract import VideoWriter
from smartcam.video import LocalVideo

logger = logging.getLogger(__name__)


class FfmpegVideoWriter(VideoWriter):
  """ opencv2 video writer """

  def __init__(self, queue, fps, path=None,
    cloud_writer=None):
    multiprocessing.Process.__init__(self)
    self.queue = queue
    self.fps = fps
    if path is not None:
      self.path = path
    else:
      self.path = os.path.join(os.path.expanduser('~'), 'Videos')
    # may still be None:
    self.cloud_writer = cloud_writer

  def get_writer(self, frame, ext='avi', is_color=True):
    ''' pass first frame of video, return writer function '''

    logger.debug("called get_writer")
    width = frame.width
    height = frame.height
    start_frame = frame
    last_frame = None
    file_prefix = frame.time.isoformat()
    file_name = "%s.%s" % (file_prefix, ext)
    full_path = os.path.join(self.path, file_name)

    p = subprocess.Popen([
      'ffmpeg', '-y', '-f', 'image2pipe', '-r', str(self.fps),
      '-s', '%sx%s' % (width, height), '-i', '-',
      '-crf', "0", '-vcodec', 'libx264', '-f', 'mp4', full_path ],
       stdin=subprocess.PIPE)

    def writer(frame):
      ''' write frames to video, optionally write video to cloud '''
      logger.debug("writing frame")
      nonlocal last_frame
      if frame is None:
        logger.debug("received null frame")
        p.stdin.close()
        p.wait()
        local_video = LocalVideo(start_frame.time,
          last_frame.time,
          width,
          height,
          full_path
        )
        if self.cloud_writer is not None:
          self.cloud_writer.write_video(local_video)
        return
      last_frame = frame
      buf = frame.encode()
      buf.seek(0)
      p.stdin.write(buf.read())

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
        logger.debug('instantiating writer')
        writer = self.get_writer(frame, ext='mp4')
      writer(frame)
