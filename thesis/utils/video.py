from django.conf import settings

import numpy
import cv2
import sys
import csv


class Video:

    def __init__(self, f):
        self.f = f
        self.name = f.temporary_file_path()
        self.faces = []
        self.labels = []
        self.face_cascade = cv2.CascadeClassifier('/home/yiorgos/Documents/opencvFaceRec/haarcascade_frontalface_default.xml')


    def printName(self):
        print "This is the video name: ", self.name
        return  str(self.name)


    def detectFaces(self):
    
        cap = cv2.VideoCapture(self.name)
    
        if not(cap.isOpened()):
            return HttpResponse('Video opened')
        
        while(cap.isOpened()):
            retval, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            for(x,y,w,h) in faces:
                cv2.rectangle(frame, (x,y), (x+w, y+h), (255,0,0),2)
            self.predictFaces(frame, faces)

            #cv2.namedWindow('img', cv2.WINDOW_NORMAL)
            #cv2.imshow('img', frame)
            if cv2.waitKey(20) & 0xFF == ord('q'):
                break

        cap.release()
        #cv2.waitKey(0)
        cv2.destroyAllWindows()


    def initializeRecognizer(self):
        self.recognizer = cv2.face.createLBPHFaceRecognizer()
        self.recognizer.train(self.faces, numpy.array(self.labels))


    def predictFaces(self, org_img, frames):
            gray_frame = cv2.cvtColor(org_img, cv2.COLOR_BGR2GRAY)
            for (x,y,w,h) in frames:
                nbr_pred, conf = self.recognizer.predict(gray_frame[y: y+h, x: x+w])
                print str(nbr_pred)


    #def train(self):

    def read_csv_file(self, path):
        path = settings.STATIC_PATH + "/faces.csv"
        img_path = settings.STATIC_PATH + "/"
        with open(path, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for row in reader: 
                #print img_path+str(row[0])
                image = cv2.imread(img_path + str(row[0]))
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                for (x,y,w,h) in faces: 
                    self.faces.append(gray[y:y+h, x:x+w])
                    self.labels.append(int(row[1]))
                   # cv2.imshow("adding image to set...", image[y:y+h, x:x+w])
                   # cv2.waitKey(30)

