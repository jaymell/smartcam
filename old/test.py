#!/usr/bin/env python
 
import cv2
import cv2.cv
import time
import reader

video = cv2.VideoCapture(reader.get_device());
ret, frame = video.read()
frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
time.sleep(2)
ret, frame2 = video.read()
frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
delta = cv2.absdiff(frame, frame2)
thresh = cv2.threshold(delta, 50, 255, cv2.THRESH_BINARY)[1]
thresh = cv2.dilate(thresh, None, iterations=2)
(contours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
video.release()
