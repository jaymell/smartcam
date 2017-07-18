from smartcam.abstract import CloudWriter
import boto3
import s3transfer
import logging
import os

logger = logging.getLogger(__name__)

class S3Writer(CloudWriter):
  ''' implements CloudWriter interface '''

  def __init__(self, region, bucket):
    self.region = region
    self.bucket = bucket

  def write(self, path):
    logger.debug("Writing to s3")
    client = boto3.client('s3', self.region)
    transfer = s3transfer.S3Transfer(client)
    transfer.upload_file(path, self.bucket, os.path.basename(path))
