import Queue
import threading
import logging

class QueueHandler(threading.Thread):
  """ provides queue for inputting images,
      and puts images onto queues for image
      and video processing """

  def __init__(self, video_queue, image_queue):
    self._queue = Queue.Queue()
    self._image_queue = image_queue
    self._video_queue = video_queue
    threading.Thread.__init__(self)

  def put(self, item):
    """ add item to queues """
    self._queue.put(item)

  def run(self):
    while True:
      frame = self._queue.get()
      try:
        self._video_queue.put(frame)
      except Exception as e:
        logging.error("failed to put image on video queue: %s" % e)
      try:
        # self._image_queue.put(image)
        pass
      except Exception as e:
        logging.error("failed to put image on image queue: %s" % e)
