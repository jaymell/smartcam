from smartcam.abstract import CloudWriter
import logging

logger = logging.getLogger(__name__)

class S3Writer(CloudWriter):
  ''' implements CloudWriter interface '''

  def __init__(self):
    pass

  def write(self, path):
    logger.debug("Aint writin shit")
    pass
