from django.conf import settings
from clock import Clock
from recognizers import Recognizer

import numpy
import cv2
import sys
import csv
import timeit


class Video:

    def __init__(self, path):
        # Path of the video file
        self.video_path = path
        # Face Training set of the recognizer
        self.faces_db = []
        # self.all_face_frames = []
        # Array with all the labels of the people from the face db
        self.labels = []
        # Dictionary holding the label as a key and name of the person as value
        self.face_labelsDict = {}
        # Classifiers for detectMultiScale() face detector
        self.face_cascade = cv2.CascadeClassifier(settings.STATIC_PATH + '/haarcascade_frontalface_alt2.xml')
        self.profile_cascade = cv2.CascadeClassifier(settings.STATIC_PATH + '/haarcascade_profileface.xml')

    def setRecognizer(self, name):
        # Read CSV face file and populate Face training set and labels
        self.read_csv_file(recogn=name)
        self.recognizer = Recognizer(name, self.faces_db, self.labels, self.face_labelsDict)


    def printName(self):
        print "This is the video name: ", self.video_path
        return  str(self.video_path)


    @Clock.time
    def detectFaces(self, useRecognition=False):

        print 'Start reading and writing frames'

        cap = cv2.VideoCapture(self.video_path)
        fourcc = cap.get(cv2.CAP_PROP_FOURCC)
        fps = cap.get(cv2.CAP_PROP_FPS)
        #fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter('static/images/output.mp4', int(fourcc), fps, (640, 480))

        # Face/Profiles Rectangles lists
        all_frames_face_rects = []
        previous_frame_face_rects = []

        if not(cap.isOpened()):
            return HttpResponse('Video not opened')
        
        while(cap.isOpened()):
            retval, frame = cap.read()
            if not frame is None: 
                # Get the current frame in grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                out.release()
                cap.release()
                return

            # Faces and Profile rects discovered at the current frame
            current_faces = []

            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3,
                    minNeighbors=4, minSize=(60, 60))
            profiles = self.profile_cascade.detectMultiScale(gray, scaleFactor=1.3,
                    minNeighbors=4, minSize=(60, 60))
            #__throw_overlapping(profiles)
            if len(faces) > 0:
                all_frames_face_rects.extend(faces)
                current_faces.extend(faces)
            if len(profiles) > 0:
                all_frames_face_rects.extend(profiles)
                current_faces.extend(profiles)

            # Get copy of the current colored frame and
            # draw all the rectangles of possible faces on the frame 
            frame_with_faces = frame.copy()
            for (x,y,w,h) in current_faces:
                cv2.rectangle(frame_with_faces, (x,y), (x+w, y+h), (0,0,255),2)
                # Predict possible faces on the original frame
                if useRecognition:
                    faceName = self.recognizer.predictFaces(gray, (x,y,w,h))
                    if faceName:
                        cv2.putText(frame_with_faces, faceName, (x, y-10), 
                                    cv2.FONT_HERSHEY_PLAIN, 1.0, (0, 0, 255), 3)

            # Write frame to video file
            scaled_frame_with_faces = cv2.resize(frame_with_faces, (640, 480))
            out.write(scaled_frame_with_faces)

        out.release()
        cap.release()
    

    def read_csv_file(self, recogn, path=""):
        path = settings.STATIC_PATH + "/faces.csv"
        img_path = settings.STATIC_PATH + "/"
        with open(path, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for row in reader: 
                #print img_path+str(row[0])
                self.face_labelsDict[int(row[1])] = str(row[0]).split('/')[1]
                image = cv2.imread(img_path + str(row[0]))
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                if recogn == 'LBPH':
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 6)
                    for (x,y,w,h) in faces: 
                        self.faces_db.append(gray[y:y+h, x:x+w])
                        self.labels.append(int(row[1]))
                else:
                    self.faces_db.append(cv2.resize(gray, (80, 80)))
                    self.labels.append(int(row[1]))
        print self.face_labelsDict

