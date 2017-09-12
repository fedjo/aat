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
from clock import Clock
import subprocess
from subprocess import PIPE


log = logging.getLogger(__name__)


def create_ui_video_name(filename, recognizer):
    if not recognizer:
        recognizer = 'DET-ONLY'

    if isinstance(filename, TemporaryUploadedFile):
        filepath = filename.temporary_file_path()
    else:
        filepath = filename

    head, tail = os.path.split(filepath)
    name = tail.os.path.split('.')[0]
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
        self.recognizer = Recognizer(name,
                                     self.faces_db,
                                     self.labels,
                                     self.face_labelsDict)

    def printName(self):
        log.debug("This is the video name: {}".format(self.video_path))
        return str(self.video_path)

    @Clock.time
    def detectFaces(self, scale, neighbors, minx, miny, useRecognition=False):

        log.debug('Start reading and writing frames')

        middle_name = ""
        if hasattr(self, 'recognizer'):
            middle_name = self.recognizer.recongnName
        video_store_path = create_ui_video_name(self.video_path, middle_name)
        log.debug(video_store_path)

        cap = cv2.VideoCapture(self.video_path)
        fourcc = cap.get(cv2.CAP_PROP_FOURCC)
        fps = cap.get(cv2.CAP_PROP_FPS)
        # fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(video_store_path, int(fourcc), fps, (640, 480))

        # Face/Profiles Rectangles lists
        all_frames_face_rects = []
        previous_frame_face_rects = []

        if not(cap.isOpened()):
            return HttpResponse('Video not opened')

        detection_time = 0
        recognition_time = 0
        i = 0
        frames_temp_path = os.path.join(settings.STATIC_ROOT,
                                        'obj-detect-frames')
        if os.path.exists(frames_temp_path):
            shutil.rmtree(frames_temp_path)
        os.mkdir(frames_temp_path)
        while(cap.isOpened()):
            retval, frame = cap.read()
            if frame:
                # Get the current frame in grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                f = open(os.path.join(settings.MEDIA_ROOT,
                                      'timelapse.log'), 'a')
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
                frame_name = os.path.join(frames_temp_path,
                                          'frame' + str(i / 50) + '.png')
                cv2.imwrite(frame_name, frame)

            # Faces and Profile rects discovered at the current frame
            current_faces = []

            # faces = self.face_cascade.detectMultiScale(gray, scaleFactor=scale,
            #        minNeighbors=neighbors, minSize=(minx, miny))
            # profiles = self.profile_cascade.detectMultiScale(gray, scaleFactor=scale,
            #        minNeighbors=neighbors, minSize=(minx, miny))

            # optional implementation to use all/selected haar cascades
            det_start = time.time()
            for c in self.haarcascades:
                current_faces.extend(
                        c.detectMultiScale(gray, scaleFactor=float(scale),
                                           minNeighbors=int(neighbors),
                                           minSize=(int(minx), int(miny))))
            det_end = time.time()
            detection_time += det_end - det_start

            # __throw_overlapping(profiles)
            # if len(faces) > 0:
            #   all_frames_face_rects.extend(faces)
            #   current_faces.extend(faces)
            # if len(profiles) > 0:
            #   all_frames_face_rects.extend(profiles)
            #   current_faces.extend(profiles)

            # Get copy of the current colored frame and
            # draw all the rectangles of possible faces on the frame
            frame_with_faces = frame.copy()
            rec_start = time.time()
            for (x, y, w, h) in current_faces:
                cv2.rectangle(frame_with_faces,
                              (x, y),
                              (x+w, y+h),
                              (0, 0, 255),
                              4)
                # Predict possible faces on the original frame
                faceName = 'person'
                if useRecognition:
                    faceName = self.recognizer.predictFaces(gray, (x, y, w, h))
                    if not faceName:
                        faceName = 'person'
                size = cv2.getTextSize(faceName,
                                       cv2.FONT_HERSHEY_PLAIN, 1.0, 1)[0]
                cv2.rectangle(frame_with_faces,
                              (x, y-size[1]-3),
                              (x+size[0]+4, y+3),
                              (0, 0, 255),
                              -1)
                cv2.putText(frame_with_faces, faceName, (x, y-2),
                            cv2.FONT_HERSHEY_PLAIN, 1.0, (255, 255, 255), 1)

            rec_end = time.time()
            recognition_time += rec_end - rec_start

            # Write frame to video file
            scaled_frame_with_faces = cv2.resize(frame_with_faces, (640, 480))
            out.write(scaled_frame_with_faces)
            i += 1

        out.release()
        cap.release()
        return

    @Clock.time
    def perform_obj_detection(self):
        frames_temp_path = os.path.join(settings.STATIC_ROOT,
                                        'obj-detect-frames')
        cmd = ['objdetect']
        detectd_frames = dict()
        for frame_name in os.listdir(frames_temp_path):
            try:
                cmd.append(os.path.join(frames_temp_path, frame_name))
                p = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
                cmd.pop()
                if stdout:
                    objclass = stdout[stdout.find('\'')+1:stdout.find('Probability')-2]
                    probability = stdout[stdout.find('Probability')+13:stdout.find('%')+1]
                    detectd_frames[frame_name] = (objclass, probability)
            except:
                log.error("Unexpected error: {}".format(sys.exc_info()[0]))
                raise
        return detectd_frames

    def read_csv_file(self, recogn, path=""):
        path = settings.STATIC_ROOT + "/faces.csv"
        img_path = settings.STATIC_ROOT + "/"
        with open(path, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for row in reader:
                self.face_labelsDict[int(row[1])] = str(row[0]).os.path.split('/')[2]
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
