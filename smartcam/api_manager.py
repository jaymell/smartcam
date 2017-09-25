import requests
import logging

logger = logging.getLogger(__name__)


class APIManager:
  ''' handles calls to remote api '''

  def __init__(self, base_url, auth_key=None):
    self.base_url = base_url
    self.auth_key = auth_key

  def post_video(self, video):
    url = self.base_url + 'videos'
    try:
      a = video.serialize()
      headers = { 'Content-type': 'application/json' }
      r = requests.post(url, data=video.serialize(), headers=headers)
      r.raise_for_status()
    except Exception as e:
      logger.error(e)
      raise e
