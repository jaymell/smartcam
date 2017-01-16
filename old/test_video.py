#!/usr/bin/env python
 
import cv2
import cv2.cv
import time
import reader

if __name__ == '__main__' :
 
    video = cv2.VideoCapture(reader.get_device());
    writer = cv2.VideoWriter('/tmp/out.avi', cv2.cv.CV_FOURCC('M','J','P','G'), 14.0, (640,480), True)
    # Number of frames to capture
    num_frames = 100;
 
    # Start time
    start = time.time()
    # Grab a few frames
    for i in xrange(0, num_frames):
        ret, frame = video.read()
        print(frame.shape)
        # img = cv2.imread(frame, 0)
        # writer.write(img)
        writer.write(frame)
    # Release video
    video.release()
    
