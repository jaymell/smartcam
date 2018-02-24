import json
import datetime


def convert_time(t):
  epoch = datetime.datetime.utcfromtimestamp(0)
  return (t - epoch).total_seconds() * 1000.0


class Video:

  def __init__(self, camera_id, start, end, width, height):
    self.camera_id = camera_id
    self._start = start
    self.width = width
    self.height = height
    self._end = end

  @property
  def start(self):
    return self._start

  @property
  def end(self):
    return self._end


class LocalVideo(Video):

  def __init__(self, camera_id, start, end, width, height, path):
    self.path = path
    super().__init__(camera_id, start, end, width, height)


class RemoteVideo(Video):
  ''' video object -- primarily for sending to remote api --
      this should match most cloud storage options -- s3,
      gcs, azure, etc. '''

  def __init__(self, camera_id, start, end, width, height, bucket, key, region=None):
    self.bucket = bucket
    self.key = key
    self.region = region
    super().__init__(camera_id, start, end, width, height)

  def serialize(self):
    return json.dumps({
      'camera_id': self.camera_id,
      'start': convert_time(self.start),
      'end': convert_time(self.end),
      'width': self.width,
      'height': self.height,
      'bucket': self.bucket,
      'key': self.key,
      'region': self.region
    }, ensure_ascii=False)



