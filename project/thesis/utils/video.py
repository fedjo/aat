from django.conf import settings
from django.http import HttpResponse
from django.core.files.uploadedfile import TemporaryUploadedFile
from recognizers import Recognizer

import os
import cv2
import csv
import sys
import time
import shutil
import logging
from celery import chain
from clock import Clock

from thesis.tasks import face_detection, object_detection


log = logging.getLogger(__name__)


def create_ui_video_name(filename, recognizer):
    if not recognizer:
        recognizer = 'DET-ONLY'

    if isinstance(filename, TemporaryUploadedFile):
        filepath = filename.temporary_file_path()
    else:
        filepath = filename

    head, tail = os.path.split(filepath)
    name = tail.split('.')[0]
    return os.path.join(settings.STATIC_ROOT, name + '-' + recognizer + '.mp4')


class Video:

    def __init__(self, path,
                 cascades=['haarcascade_frontalface_alt2.xml',
                           'haarcascade_profileface.xml',
                           'haarcascade_frontalcatface_extended.xml',
                           'haarcascade_frontalcatface.xml',
                           'haarcascade_frontalface_default.xml']):
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
        self.face_cascade = cv2.CascadeClassifier(
                os.path.join(settings.STATIC_ROOT, 'haar_cascades',
                             'haarcascade_frontalface_alt2.xml'))
        self.profile_cascade = cv2.CascadeClassifier(
                os.path.join(settings.STATIC_ROOT, 'haar_cascades',
                             'haarcascade_profileface.xml'))

        # optional implementation to use all/selected haar cascades
        cascadesdir = os.path.join(settings.STATIC_ROOT, 'haar_cascades')
        self.haarcascades = [cv2.CascadeClassifier(
            os.path.join(cascadesdir, x))
            for x in os.listdir(cascadesdir) if x in cascades]

    def setRecognizer(self, name):
        # Read CSV face file and populate Face training set and labels
        self.read_csv_file(recogn=name)
        self.myrecognizer = Recognizer(name)
        self.myrecognizer.train(self.faces_db, self.labels)

    def printName(self):
        log.debug("This is the video name: {}".format(self.video_path))
        return str(self.video_path)

    @Clock.time
    def detectFaces(self, scale, neighbors, minx, miny, useRecognition=False):

        log.debug('Start reading and writing frames')

        middle_name = ""
        if hasattr(self, 'myrecognizer'):
            middle_name = self.myrecognizer.recongnName
        video_store_path = create_ui_video_name(self.video_path, middle_name)
        log.debug(video_store_path)

        #face_detection(self.video_path, video_store_path, self, recognizer,
                #scale, neighbors, minx, miny, useRecognition).delay()
        chain(face_detection.s(self.video_path, video_store_path,
                               #self.myrecognizer.as_dict(), self.face_labelsDict,
                               self.haarcascades,
                               scale, neighbors, minx, miny,
                               useRecognition), object_detection.s())()
        


    #@Clock.time
    #def perform_obj_detection(self):
        #objects = object_detecion.delay().get()

    def read_csv_file(self, recogn, path=""):
        path = settings.STATIC_ROOT + "/faces.csv"
        img_path = settings.STATIC_ROOT + "/"
        with open(path, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for row in reader:
                self.face_labelsDict[int(row[1])] = str(row[0]).split('/')[2]
                log.debug((img_path + str(row[0])))
                image = cv2.imread(img_path + str(row[0]))
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                if recogn == 'LBPH':
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 6)
                    for (x, y, w, h) in faces:
                        self.faces_db.append(gray[y:y+h, x:x+w])
                        self.labels.append(int(row[1]))
                else:
                    self.faces_db.append(cv2.resize(gray, (80, 80)))
                    self.labels.append(int(row[1]))
        log.debug(self.face_labelsDict)
