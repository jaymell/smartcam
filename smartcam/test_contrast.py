#!/usr/bin/env python3
 
import cv2
import numpy as np
import matplotlib.pyplot as plt
from main import get_device
from motion_detector import equalize_image

video = cv2.VideoCapture(get_device(use_default=True));
_, img = video.read()

img = equalize_image(img)
cv2.imshow('barf', img)
cv2.waitKey(10000)
#cv2.destroyWindow('barf')
