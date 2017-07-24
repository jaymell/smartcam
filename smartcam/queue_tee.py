import queue
import multiprocessing
import logging
import time

logger = logging.getLogger(__name__)


class QueueTee(multiprocessing.Process):
  ''' read from in_queue
      and put it onto out_queues
  '''

  def __init__(self, in_queue, out_queues):
    multiprocessing.Process.__init__(self)
    self.in_queue = in_queue
    self.out_queues = out_queues
    self.daemon = True

  def run(self):
    logger.debug("starting queue_tee run loop")
    while True:
      try:
        frame = self.in_queue.get()
      except queue.Empty:
        continue
      for q in self.out_queues:
        try:
          q.put(frame)
        except Exception as e:
          logger.error("failed to put image on queue: %s" % e)
