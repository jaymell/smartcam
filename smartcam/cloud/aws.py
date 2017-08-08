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
    self.client = boto3.client('s3', self.region)

  def write_file(self, path, remote_path):
    logger.debug("write_file: writing to s3")
    transfer = s3transfer.S3Transfer(self.client)
    transfer.upload_file(path, self.bucket, remote_path)

  def write_fileobj(self, fileobj, remote_path):
    logger.debug("write_fileobj: writing to s3")
    self.client.upload_fileobj(fileobj, self.bucket, remote_path)
