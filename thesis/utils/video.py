import numpy as np
import cv2
import sys


class Video:

    def __init__(self, f):
        self.f = f
        self.name = f.temporary_file_path()


    def printName(self):
        print "This is the video name: ", self.name
        return  str(self.name)


    def detectFaces(self):
        face_cascade = cv2.CascadeClassifier('/home/yiorgos/Documents/opencvFaceRec/haarcascade_frontalface_default.xml')
    
        cap = cv2.VideoCapture(self.name)
    
        if not(cap.isOpened()):
            return HttpResponse('Video opened')
        
        while(cap.isOpened()):
            retval, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            for(x,y,w,h) in faces:
                cv2.rectangle(frame, (x,y), (x+w, y+h), (255,0,0),2)

            cv2.namedWindow('img', cv2.WINDOW_NORMAL)
            cv2.imshow('img', frame)
            if cv2.waitKey(20) & 0xFF == ord('q'):
                break

        cap.release()
        #cv2.waitKey(0)
        cv2.destroyAllWindows()

    def predictFaces(self):
        recognizer = cv2.createLBPHFaceRecognizer()

        

