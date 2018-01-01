from multiprocessing import Queue as _Queue
import logging

logger = logging.getLogger(__name__)

class Queue():
  def __init__(self, label, debug=False):
    self.label = label
    self.debug = debug
    self._queue = _Queue()
    self.i = 0

  def get(self):
    interval = 20
    item = self._queue.get()
    if self.debug:
      self.i = self.i + 1
      if self.i % interval == 0:
        self.i = 0
        logger.debug("%s queue depth: %s" % (self.label, self._queue.qsize()))
    return item

  def put(self, item):
    return self._queue.put(item)
