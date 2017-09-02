from smartcam.abstract import CloudWriter
import boto3
import s3transfer
import logging
import os
import string
import random

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


class KinesisWriter(CloudWriter):
  def __init__(self, region, stream):
    self.region = region
    self.stream = stream
    self.client = boto3.client('kinesis', self.region)

  def write_file(self, file, dest):
    """ dest is not used """
    pass

  def get_partition_key(self):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))


  def write_fileobj(self, fileobj, dest):
    """ dest is not used """
    # pass
    response = self.client.put_record(
        StreamName=self.stream,
        Data=fileobj.read(),
        PartitionKey=self.get_partition_key()
    )

  def write_str(self, src_str, dest):
    """ dest is not used """
    # pass
    response = self.client.put_record(
        StreamName=self.stream,
        Data=src_str,
        PartitionKey=self.get_partition_key()
    )

