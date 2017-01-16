#!/usr/bin/env python
 
import cv2
import cv2.cv
import time
import reader

if __name__ == '__main__' :
  video = cv2.VideoCapture(reader.get_device());
  ret, frame = video.read()
  cv2.imwrite('/tmp/out.jpeg', frame)
  video.release()
