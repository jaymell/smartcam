import queue

class QueueHandler:
  """ provides queue for inputting images,
      and puts images onto queues for image
      and video processing """

  def __init__(self):
    self._queue = queue.queue()

  def put(self, item):
  	""" add item to queues """