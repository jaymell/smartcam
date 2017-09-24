class Video:
  ''' video object -- primarily for sending to remote api '''

  def __init__(self, start, end, width, height):
    self.start = start
    self.end = end
    self.width = width
    self.height = height

