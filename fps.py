#!/usr/bin/env python3
 
import cv2
import time
import sys

if __name__ == '__main__' :
 
    # Start default camera
    video = cv2.VideoCapture(0)
 
    # Number of frames to capture
    num_frames = 1200;
     
    print("Capturing {0} frames".format(num_frames))
 
    # Start time
    start = time.time()
     
    # Grab a few frames
    for i in range(0, num_frames) :
        ret, frame = video.read()
        if ret is not True: 
          print("failed")
          sys.exit(1)
 
     
    # End time
    end = time.time()
 
    # Time elapsed
    seconds = end - start
    print("Time taken : {0} seconds".format(seconds))
 
    # Calculate frames per second
    fps  = num_frames / seconds;
    print("Estimated frames per second : {0}".format(fps))
 
    # Release video
    video.release()
