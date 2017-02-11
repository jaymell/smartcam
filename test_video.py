#!/usr/bin/env python3
 
import cv2
import time
from main import get_device

if __name__ == '__main__' :
 
    fmt = 'MP42'
    video = cv2.VideoCapture(get_device(use_default=False));
    writer = cv2.VideoWriter('/tmp/out', cv2.VideoWriter_fourcc(*fmt), 14.0, (640,480), True)
    # Number of frames to capture
    num_frames = 100;
 
    # Start time
    start = time.time()
    # Grab a few frames
    for i in range(0, num_frames):
        ret, frame = video.read()
        print(frame.shape)
        # img = cv2.imread(frame, 0)
        # writer.write(img)
        writer.write(frame)
    # Release video
    video.release()
    
