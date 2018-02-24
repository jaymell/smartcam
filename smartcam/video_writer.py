import logging
import multiprocessing
import os
import queue
import subprocess
from threading import Thread, Lock
import cv2
from PIL import Image
from smartcam.abstract import VideoWriter
from smartcam.video import RemoteVideo

logger = logging.getLogger(__name__)


class FFMpegProcess:

  def __init__(self, fps, width, height, pipe, is_color=True):
    """ pass first frame of video, return ffmpeg process """
    logger.debug("instantiating FFMpegProcess")
    self.pipe = open(pipe, 'wb')
    self.p = subprocess.Popen([
      'ffmpeg', '-y', '-f', 'image2pipe', '-r', str(fps),
      '-s', '%sx%s' % (width, height), '-i', '-',
      '-crf', "0", '-vcodec', 'libx264', '-f', 'matroska', "-" ],
       stdin=subprocess.PIPE, stdout=self.pipe)

  def write(self, frame):
    """ write frame to ffmpeg """

    logger.debug("writing frame")
    last_frame = frame
    buf = frame.encode()
    buf.seek(0)
    self.p.stdin.write(buf.read())

  def close(self):
    logger.debug("FFMpegProcess: closing")
    try:
      self.p.stdin.close()
      self.p.wait()
      self.pipe.close()
    except Exception as e:
      logger.error("Failed to close FFMpeg: %s" % e)

  def __del__(self):
    self.close()


def chunk_generator(pipe):
  """ return generator function """
  CHUNK_SIZE = 1048576
  while True:
    data = pipe.read(CHUNK_SIZE)
    if len(data) == 0:
      logger.debug("chunk_generator no data read: returning")
      return
    logger.debug("chunk_generator read %s bytes" % len(data))
    yield data


class VideoManager:
  ''' manage ffmpeg and remote api calls '''
  def __init__(self, fps, api_manager, frame):
    self.r, self.w = os.pipe()
    self.first_frame = frame
    self.current_frame = frame
    self.ffmpeg = FFMpegProcess(fps, frame.width, frame.height, self.w)
    self.api_manager = api_manager
    self.lock = Lock()
    self.readfh = open(self.r, 'rb')
    Thread(target=self.post_video,
      args=(chunk_generator(self.readfh),),
      name='api_manager_video_post').start()

  def post_video(self, generator):
    """ post video binary then metadata, hold
        lock to prevent pipe from being closed from
        other thread """
    try:
      with self.lock:
        resp = self.api_manager.post_video_data(generator)
        self.api_manager.post_video(RemoteVideo(
            self.first_frame.id,
            self.first_frame.time,
            self.current_frame.time,
            self.first_frame.width,
            self.first_frame.height,
            resp['bucket'],
            resp['key'],
            resp['region']))
    except Exception as e:
      logger.error("ERROR: Failed to post video: %s" % e)

  def on_next(self, frame):
    self.current_frame = frame
    self.ffmpeg.write(frame)

  def on_completed(self):
    """ this should block until post_video is done """
    self.ffmpeg.close()
    with self.lock:
      self.ffmpeg = None
      self.readfh.close()


class VideoWriterImpl(VideoWriter):

  def __init__(self, queue, fps, api_manager):
    multiprocessing.Process.__init__(self)
    self.name =  VideoWriterImpl.__name__
    self.queue = queue
    self.fps = fps
    self.api_manager = api_manager

  def run(self):
    vid_man = None
    while True:
      try:
        frame = self.queue.get()
        if vid_man is None:
          vid_man = VideoManager(self.fps, self.api_manager, frame)
        if frame is not None:
          vid_man.on_next(frame)
        else:
          vid_man.on_completed()
          vid_man = None
      except Exception as e:
        logger.error("ERROR: Failed to handle frame: %s" % e)
