import os
import sys

import numpy as np
import cv2

def main(dir):
    face_cascade = cv2.CascadeClassifier('/facerec/project/thesis/static/haar_cascades/haarcascade_frontalface_alt2.xml')
    for i in os.listdir(dir):
        imgfile = os.path.join(dir, i)
        imgfilename, imgextension = os.path.splitext(imgfile)
        img = cv2.imread(imgfile)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, 1.1, 8)
        if len(faces) > 0:
            (x, y ,w, h) = faces[0]
            roi_face = img[y:y+h, x:x+w]
            cv2.imwrite(imgfile, roi_face)


if __name__ == "__main__":
    main(sys.argv[1])

