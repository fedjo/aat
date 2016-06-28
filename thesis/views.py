from django.shortcuts import render
from django.http import HttpResponse

import numpy as np
import cv2

# Create your views here.

def index(request):
    face_cascade = cv2.CascadeClassifier('/home/yiorgos/Documents/opencvFaceRec/haarcascade_frontalface_default.xml')

    #img = cv2.imread('/home/yiorgos/Documents/opencvFaceRec/lena.png')
    #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    cap = cv2.VideoCapture('/home/yiorgos/Documents/opencvFaceRec/happy.avi')

    if not(cap.isOpened()):
        return HttpResponse('Video opened')

    for i in range(230,1000):
        retval, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for(x,y,w,h) in faces:
            cv2.rectangle(frame, (x,y), (x+w, y+h), (255,0,0),2)

        cv2.namedWindow('img' + str(i), cv2.WINDOW_NORMAL)
        cv2.imshow('img'+ str(i), frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        cv2.waitKey(0)
        cv2.destroyAllWindows()


    return HttpResponse("Hello my thesis")
