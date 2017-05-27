from django.conf import settings
from django.http import HttpResponse
from django.core.files.uploadedfile import TemporaryUploadedFile
from clock import Clock
from recognizers import Recognizer

from os import mkdir, listdir, chdir
from os.path import splitext, join, split, exists
import subprocess
from subprocess import PIPE

import numpy
import cv2
import sys
import csv
import timeit
import time
import shutil

def create_ui_video_name(filename, recognizer):
    if not recognizer:
        recognizer = 'DET-ONLY'

    if isinstance(filename, TemporaryUploadedFile):
        filepath = filename.temporary_file_path()
    else:
        filepath = filename

    head, tail = split(filepath)
    name = tail.split('.')[0]
    return join(settings.STATIC_PATH, name + '-' + recognizer + '.mp4')


class Video:

    def __init__(self, path, cascades=['haarcascade_frontalface_alt2.xml',
        'haarcascade_profileface.xml', 'haarcascade_frontalcatface_extended.xml',
        'haarcascade_frontalcatface.xml', 'haarcascade_frontalface_default.xml']):
        # Path of the video file
        if isinstance(path, TemporaryUploadedFile):
            self.video_path = path.temporary_file_path()
        else:
            self.video_path = path
        # Face Training set of the recognizer
        self.faces_db = []
        # self.all_face_frames = []
        # Array with all the labels of the people from the face db
        self.labels = []
        # Dictionary holding the label as a key and name of the person as value
        self.face_labelsDict = {}
        # Classifiers for detectMultiScale() face detector
        self.face_cascade = cv2.CascadeClassifier(join(settings.STATIC_PATH, \
            'haar_cascades', 'haarcascade_frontalface_alt2.xml'))
        self.profile_cascade = cv2.CascadeClassifier(join(settings.STATIC_PATH, \
            'haar_cascades', 'haarcascade_profileface.xml'))

        # optional implementation to use all/selected haar cascades
        cascadesdir = join(settings.STATIC_PATH, 'haar_cascades')
        self.haarcascades = \
                [ cv2.CascadeClassifier(join(cascadesdir, x)) for x in listdir(cascadesdir) if x in cascades ]

    def setRecognizer(self, name):
        # Read CSV face file and populate Face training set and labels
        self.read_csv_file(recogn=name)
        self.recognizer = Recognizer(name, self.faces_db, self.labels, self.face_labelsDict)


    def printName(self):
        print "This is the video name: ", self.video_path
        return  str(self.video_path)


    @Clock.time
    def detectFaces(self, scale, neighbors, minx, miny, useRecognition=False):

        print 'Start reading and writing frames'

        middle_name = ""
        if hasattr(self, 'recognizer'):
            middle_name = self.recognizer.recongnName
        video_store_path = create_ui_video_name(self.video_path, middle_name)
        print video_store_path

        cap = cv2.VideoCapture(self.video_path)
        fourcc = cap.get(cv2.CAP_PROP_FOURCC)
        fps = cap.get(cv2.CAP_PROP_FPS)
        #fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(video_store_path, int(fourcc), fps, (640, 480))

        # Face/Profiles Rectangles lists
        all_frames_face_rects = []
        previous_frame_face_rects = []

        if not(cap.isOpened()):
            return HttpResponse('Video not opened')

        detection_time = 0
        recognition_time = 0
        i = 0
        frames_temp_path = join(settings.STATIC_PATH, 'obj-detect-frames')
        if exists(frames_temp_path):
            shutil.rmtree(frames_temp_path)
        mkdir(frames_temp_path)
        while(cap.isOpened()):
            retval, frame = cap.read()
            if not frame is None:
                # Get the current frame in grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                f = open(settings.BASE_DIR + '/timelapse.log', 'a')
                f.write('---Detection time---\n')
                f.write('%r() %2.2f sec\n' % ('for all frames run detectMultiScale',  detection_time))
                f.write('---Recognition time---\n')
                f.write('%r() %2.2f sec\n' % ('for all faces run predictFaces',  recognition_time))
                f.close()
                out.release()
                cap.release()
                return

            # Keep every 50 frames for object detection
            if i % 50 == 0:
                frame_name = join(frames_temp_path, 'frame' + str(i / 50) + '.png')
                cv2.imwrite(frame_name, frame)

            # Faces and Profile rects discovered at the current frame
            current_faces = []

            #faces = self.face_cascade.detectMultiScale(gray, scaleFactor=scale,
                    #minNeighbors=neighbors, minSize=(minx, miny))
            #profiles = self.profile_cascade.detectMultiScale(gray, scaleFactor=scale,
                    #minNeighbors=neighbors, minSize=(minx, miny))

            # optional implementation to use all/selected haar cascades
            det_start = time.time()
            for c in self.haarcascades:
                current_faces.extend(c.detectMultiScale(gray,
                    scaleFactor=float(scale), minNeighbors=int(neighbors),
                    minSize=(int(minx), int(miny))))
            det_end = time.time()
            detection_time += det_end - det_start

            #__throw_overlapping(profiles)
            #if len(faces) > 0:
                #all_frames_face_rects.extend(faces)
                #current_faces.extend(faces)
            #if len(profiles) > 0:
                #all_frames_face_rects.extend(profiles)
                #current_faces.extend(profiles)

            # Get copy of the current colored frame and
            # draw all the rectangles of possible faces on the frame
            frame_with_faces = frame.copy()
            rec_start = time.time()
            for (x,y,w,h) in current_faces:
                cv2.rectangle(frame_with_faces, (x,y), (x+w, y+h), (0,0,255),2)
                # Predict possible faces on the original frame
                if useRecognition:
                    faceName = self.recognizer.predictFaces(gray, (x,y,w,h))
                    if faceName:
                        cv2.putText(frame_with_faces, faceName, (x, y-10),
                                    cv2.FONT_HERSHEY_PLAIN, 1.0, (0, 0, 255), 3)
            rec_end = time.time()
            recognition_time += rec_end - rec_start

            # Write frame to video file
            scaled_frame_with_faces = cv2.resize(frame_with_faces, (640, 480))
            out.write(scaled_frame_with_faces)
            i +=1

        out.release()
        cap.release()
        return



    @Clock.time
    def perform_obj_detection(self):
        frames_temp_path = join(settings.STATIC_PATH, 'obj-detect-frames')
        cmd = ['objdetect']
        detectd_frames = dict()
        for frame_name in listdir(frames_temp_path):
            try:
                cmd.append(join(frames_temp_path, frame_name))
                p = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
                cmd.pop()
                if stdout:
                    objclass = stdout[stdout.find('\'')+1:stdout.find('Probability')-2]
                    probability = stdout[stdout.find('Probability')+13:stdout.find('%')+1]
                    detectd_frames[frame_name] = (objclass, probability)
            except:
                print "Unexpected error: ", sys.exc_info()[0]
                raise
        return detectd_frames


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

