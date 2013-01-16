import cv
import sys
import time
import os

if __name__ == "__main__":

    if len(sys.argv) is not 2:
        sys.exit(0)

    # redirect stderr
    r, w = os.pipe()
    os.close(sys.stderr.fileno())
    os.dup2(w, sys.stderr.fileno())

    path = sys.argv[1]
    cam = cv.CaptureFromCAM(-1)
    if not cam:
        sys.exit(0)
    cv.GrabFrame(cam)
    time.sleep(0.5)
    # take 2nd pic as previous may have bad quality
    cv.GrabFrame(cam)
    img = cv.RetrieveFrame(cam)
    if not img:
        sys.exit(0)
    imgpath = path + "/capture.jpg"
    cv.SaveImage(imgpath, img)
    print imgpath
