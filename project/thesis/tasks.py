from __future__ import absolute_import, unicode_literals

import os
import sys
import cv2
import time
import shutil
import logging
import subprocess
from subprocess import PIPE
from celery import shared_task

from django.conf import settings

from .utils.recognizers import Recognizer


log = logging.getLogger(__name__)


@shared_task(bind=True)
def face_detection(self, video_path, video_store_path,
                   #drecognizer,face_labelsDict,
                   haarcascades, scale, neighbors,
                   minx, miny, useRecognition=False):

    #recognizer = Recognizer(drecognizer['recongnName'])
    #recognizer.recognizer = drecognizer['recognizer']

    cap = cv2.VideoCapture(video_path)
    fourcc = cap.get(cv2.CAP_PROP_FOURCC)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(video_store_path, int(fourcc), fps, (640, 480))

    # Face/Profiles Rectangles lists
    all_frames_face_rects = []
    previous_frame_face_rects = []

    if not(cap.isOpened()):
        raise Exception('Cannot open video')
        return None

    detection_time = 0
    recognition_time = 0
    i = 0
    frames_temp_path = os.path.join(settings.MEDIA_ROOT,
                                    'obj-detect-frames')
    if os.path.exists(frames_temp_path):
        shutil.rmtree(frames_temp_path)
    os.mkdir(frames_temp_path)
    while(cap.isOpened()):
        retval, frame = cap.read()
        if not frame is None:
            # Get the current frame in grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            with open(os.path.join(settings.MEDIA_ROOT,
                                    'timelapse.log'), 'a') as f:
                f.write('---Detection time---\n')
                f.write('%r() %2.2f sec\n' % ('for all frames run detectMultiScale',  detection_time))
                f.write('---Recognition time---\n')
                f.write('%r() %2.2f sec\n' % ('for all faces run predictFaces',  recognition_time))
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
        for c in haarcascades:
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
                faceName = recognizer.predictFaces(gray, (x, y, w, h),
                                                   face_labelsDict)
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
    return frames_temp_path


@shared_task(bind=True)
def face_recognition(self):
    return


@shared_task(bind=True)
def object_detection(self, frames_temp_path):
    log.debug("Start detecting objects")
    if not frames_temp_path:
        frames_temp_path = os.path.join(settings.MEDIA_ROOT,
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
