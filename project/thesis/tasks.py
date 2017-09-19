from __future__ import absolute_import, unicode_literals

import os
import sys
import cv2
import time
import shutil
import logging
import subprocess
import tempfile
from subprocess import PIPE
from celery import shared_task

from django.conf import settings

from .models import Cascade
from .utils.video_utils import configure_recognizer


log = logging.getLogger(__name__)


@shared_task(bind=True)
def face_detection_recognition(self, video_path, video_store_path,
                               recognizer_name, faces_path,
                               haarcascades, scale, neighbors,
                               minx, miny,
                               has_bounding_boxes,
                               has_obj_det):

    log.debug('Trying to open video {}'.format(video_path))
    cap = cv2.VideoCapture(video_path)
    fourcc = cap.get(cv2.CAP_PROP_FOURCC)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(video_store_path, int(fourcc), fps, (640, 480))

    if not(cap.isOpened()):
        log.debug("Cannot open video path {}".format(video_path))
        raise Exception('Cannot open video')
        return ''

    if recognizer_name:
        (myrecognizer, face_labelsDict) = \
                configure_recognizer(recognizer_name, faces_path)

    detection_time = 0
    recognition_time = 0
    i = 0
    if has_obj_det:
        frames_temp_path = tempfile.mkdtemp(dir=settings.STATIC_ROOT)
        subprocess.call(['chmod', '-R', '+rx', frames_temp_path])
    else:
        frames_temp_path = ''

    log.debug('Frames temporary path is {}'.format(frames_temp_path))
    log.debug('Start reading and writing frames')
    try:
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
                return frames_temp_path

            # Keep every 50 frames for object detection
            if (frames_temp_path and i % 50 == 0):
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
            db_haarcascades = Cascade.objects.filter(pk__in=haarcascades).all()
            for c in db_haarcascades:
                cascade = cv2.CascadeClassifier(c.xml_file.path)
                current_faces.extend(
                        cascade.detectMultiScale(gray, scaleFactor=float(scale),
                                                 minNeighbors=int(neighbors),
                                                 minSize=(int(minx), int(miny))))
            det_end = time.time()
            detection_time += det_end - det_start

            # __throw_overlapping(profiles)

            if (not has_bounding_boxes and not recognizer_name):
                # Write frame to video file
                try:
                    out.write(cv2.resize(frame, (640, 480)))
                    recognition_time += 0
                    i += 1
                    continue
                except Exception as e:
                    log.error("Cannot write new frame to video")
                    log.error(str(e))

            # Measure time for recognition of faces on every frame
            rec_start = time.time()
            # Get copy of the current colored frame and
            # draw all the rectangles of possible faces on the frame
            # along with the name recognized
            frame_with_faces = frame.copy()
            for (x, y, w, h) in current_faces:
                facename_prob = 'person - NaN %'
                if recognizer_name:
                    # Predict possible faces on the original frame
                    (facename, prob) = myrecognizer.predictFaces(gray, (x, y, w, h),
                                                                 face_labelsDict)
                    facename_prob = facename + ' - ' + str(prob) + '%'
                    if not facename_prob:
                        facename_prob = 'person - NaN %'
                if has_bounding_boxes:
                    # Draw rectangle around the face
                    cv2.rectangle(frame_with_faces,
                                  (x, y),
                                  (x+w, y+h),
                                  (0, 0, 255),
                                  4)
                    size = cv2.getTextSize(facename_prob,
                                           cv2.FONT_HERSHEY_PLAIN, 1.0, 1)[0]
                    cv2.rectangle(frame_with_faces,
                                  (x, y-size[1]-3),
                                  (x+size[0]+4, y+3),
                                  (0, 0, 255),
                                  -1)
                    cv2.putText(frame_with_faces, facename_prob, (x, y-2),
                                cv2.FONT_HERSHEY_PLAIN, 1.0, (255, 255, 255), 1)

            rec_end = time.time()
            recognition_time += rec_end - rec_start

            # Write frame to video file
            try:
                out.write(cv2.resize(frame_with_faces, (640, 480)))
            except Exception as e:
                log.error("Cannot write new frame to video")
                log.error(str(e))
            i += 1

    except Exception as e:
        log.error(str(e))
        out.release()
        cap.release()
        return frames_temp_path

    out.release()
    cap.release()
    return frames_temp_path


@shared_task(bind=True)
def object_detection(self, frames_temp_path):
    log.debug("Start detecting objects")
    detectd_frames = dict()
    if not frames_temp_path:
        return detectd_frames

    cmd = ['objdetect']
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
    #shutil.rmtree(frames_temp_path)
    return (frames_temp_path, detectd_frames)


@shared_task(bind=True)
def transcribe(self, video_path):
    log.debug("Start transcribing video")

    cmd = ['autosub',  video_path]
    try:
        p = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        cmd.pop()
        log.debug(os.listdir(os.path.abspath(video_path)))
        if stdout:
            srt_path = video_path[:-4] + '.srt'
    except:
        log.error("Unexpected error: {}".format(sys.exc_info()[0]))
        raise
    #shutil.rmtree(frames_temp_path)
    cmd = ['ffmpeg', '-i', video_path, '-i', srt_path,
           '-c', 'copy', '-c:s', 'mov_text', video_path]
    try:
        p = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        cmd.pop()
        log.debug(os.listdir(os.path.abspath(video_path)))
    except:
        log.error("Unexpected error: {}".format(sys.exc_info()[0]))
        raise

    return

