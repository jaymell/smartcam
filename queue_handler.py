import Queue
import multiprocessing
import logging


logger = logging.getLogger(__name__)


class QueueHandler(multiprocessing.Process):
  """ provides queue for inputting images,
      and puts images onto queues for image
      and video processing """

  def __init__(self, video_queue, image_queue):
    multiprocessing.Process.__init__(self)
    self._queue = multiprocessing.Queue()
    self._image_queue = image_queue
    self._video_queue = video_queue
    self.daemon = True

  def put(self, item):
    """ add item to queues """
    self._queue.put(item)

  def run(self):
    logger.debug("starting queue_handler run loop")
    while True:
      logging.debug("queue_handler getting frame")
      try:
        frame = self._queue.get(block=False)
      except Queue.Empty:
        # SHOULD I PAUSE HERE?
        continue
      
      logger.debug("queue_handler got frame")
      
      try:
        self._video_queue.put(frame)
        pass
      except Exception as e:
        logger.error("failed to put image on video queue: %s" % e)
      try:
        logger.debug("put image on image queue")
        self._image_queue.put(frame)
        # pass
      except Exception as e:
        logger.error("failed to put image on image queue: %s" % e)
