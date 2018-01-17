import cv2
import logging
import os
import subprocess
from PIL import Image
import multiprocessing
import queue
import datetime
from smartcam.abstract import VideoWriter
from smartcam.video import LocalVideo

logger = logging.getLogger(__name__)


class FfmpegVideoWriter(VideoWriter):
  """ opencv2 video writer """

  def __init__(self, queue, fps, path=None, cloud_writer=None):
    multiprocessing.Process.__init__(self)
    self.name =  FfmpegVideoWriter.__name__
    self.queue = queue
    self.fps = fps
    if path is not None:
      self.path = path
    else:
      self.path = '/tmp'
    # may still be None:
    self.cloud_writer = cloud_writer

  def get_writer(self, frame, ext='avi', is_color=True):
    ''' pass first frame of video, return writer function
        and name of file '''

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
        t1 = datetime.datetime.now()
        p.stdin.close()
        t2 = datetime.datetime.now()
        logger.debug("Time to close pipe stdin: %s" % (t2-t1).total_seconds())
        p.wait()
        t3 = datetime.datetime.now()
        logger.debug("Time to p.wait(): %s" % (t3-t2).total_seconds())
        local_video = LocalVideo(start_frame.id,
          start_frame.time,
          last_frame.time,
          width,
          height,
          full_path
        )
        if self.cloud_writer is not None:
          try:
            t4 = datetime.datetime.now()
            self.cloud_writer.write_video(local_video)
            t5 = datetime.datetime.now()
            logger.debug("Time for cloud_write.write_video: %s" % (t5-t4).total_seconds())
          except Exception as e:
            logger.error("Failed to write video to cloud_writer: %s" % e)
        return
      last_frame = frame
      buf = frame.encode()
      buf.seek(0)
      t6 = datetime.datetime.now()
      p.stdin.write(buf.read())
      t7 = datetime.datetime.now()
      logger.debug("Time write video frame to pipe: %s" % (t7-t6).total_seconds())

    return writer, full_path

  def run(self):
    writer = None
    video_file = None
    while True:
      try:
        frame = self.queue.get()
      except queue.Empty:
        continue
      t1 = datetime.datetime.now()
      if frame is None:
        if writer is not None:
          logger.debug("writing null frame")
          writer(frame)
          writer = None
        if video_file is not None:
          try:
            logger.debug("deleting %s" % video_file)
            os.remove(video_file)
            t3 = datetime.datetime.now()
          except Exception as e:
            logger.error("Failed to delete video")
            raise e
        continue
      if writer is None:
        logger.debug('instantiating writer')
        t4 = datetime.datetime.now()
        writer, video_file = self.get_writer(frame, ext='mp4')
        t5 = datetime.datetime.now()
      try:
        t6 = datetime.datetime.now()
        writer(frame)
        t7 = datetime.datetime.now()
      except Exception as e:
        logger.error("Failed to write frame to video ")
        raise e