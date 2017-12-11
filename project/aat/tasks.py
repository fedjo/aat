from __future__ import absolute_import, unicode_literals

import os
import sys
import cv2
import time
import shutil
import logging
import tempfile
import subprocess
from celery import shared_task

# Tensorflow imports
import numpy as np
import tensorflow as tf
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
# ##################

from django.conf import settings

from .models import Cascade
from .utils.video_utils import configure_recognizer
from .utils.general_utils import exec_cmd


log = logging.getLogger(__name__)


@shared_task(bind=True)
def face_detection_recognition(self, video_path, video_store_path,
                               recognizer_name, faces_path,
                               haarcascades, scale, neighbors,
                               minx, miny,
                               has_bounding_boxes):

    log.debug('Trying to open video {}'.format(video_path))
    cap = cv2.VideoCapture(video_path)
    fourcc = cap.get(cv2.CAP_PROP_FOURCC)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    #out = cv2.VideoWriter(video_store_path, int(fourcc), fps, (640, 480))
    #_fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    _fourcc = 875967048 #cv2.cv.CV_FOURCC(*'MP4V')
    out = cv2.VideoWriter(video_store_path, _fourcc, fps, (640, 480))

    if not(cap.isOpened()):
        log.debug("Cannot open video path {}".format(video_path))
        raise Exception('Cannot open video')
        return ''

    txt_path = os.path.join(settings.CACHE_ROOT,
                            os.path.basename(video_store_path).split('.')[0]+'.txt')

    if recognizer_name:
        (myrecognizer, face_labelsDict) = \
                configure_recognizer(recognizer_name, 'SD_FACES', faces_path)

    detection_time = 0
    recognition_time = 0

    log.debug('Start reading and writing frames')
    faces_count = dict()
    allface_positions = dict()
    try:
        while(cap.isOpened()):
            ret_grab = cap.grab()
            if not ret_grab:
                with open(os.path.join(settings.MEDIA_ROOT,
                                       'timelapse.log'), 'a') as f:
                    f.write('---Detection time---\n')
                    f.write('%r() %2.2f sec\n' % ('for all frames run detectMultiScale',  detection_time))
                    f.write('---Recognition time---\n')
                    f.write('%r() %2.2f sec\n' % ('for all faces run predictFaces',  recognition_time))
                log.debug('Name2: {}'.format(faces_count))
                break

            # Decode the current frame
            ret, frame = cap.retrieve()
            # Get the current frame in grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Faces Mat discovered at the current frame
            current_faces = []

            # optional implementation to use all/selected haar cascades
            det_start = time.time()
            db_haarcascades = Cascade.objects.filter(pk__in=haarcascades).all()
            for c in db_haarcascades:
                cascade = cv2.CascadeClassifier(c.xml_file.path)
                current_faces.extend(cascade.detectMultiScale(gray, scaleFactor=float(scale),
                                                 minNeighbors=int(neighbors),
                                                 minSize=(int(minx), int(miny))))
                allface_positions[cap.get(1)] = [ a.tolist() for a in current_faces ]
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
                    if not facename:
                        facename_prob = 'person - NaN %'
                    else:
                        if facename in faces_count:
                            faces_count[facename] += 1
                        else:
                            faces_count[facename] = 1
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

    except Exception as e:
        log.error(str(e))

    out.release()
    cap.release()

    # TODO
    # This piece of code has to be moved whitin the while loo
    log.debug("Writing file {}".format(txt_path))
    #log.debug(allface_positions)
    for k, v in allface_positions.iteritems():
        for (x,y,w,h) in v:
            with open(txt_path, 'a') as a:
                a.write("Frame {}:\n".format(k))
                a.write("Face in position: ({}, {})\n".format(x, y))
                a.write("Dimensions: w = {}, h = {}\n".format(w, h))
    for k, f in faces_count.iteritems():
        with open(txt_path, 'a') as a:
            a.write("Face {} found {} times:\n".format(k, f))

    return allface_positions, faces_count


@shared_task(bind=True)
def object_detection2(self, video_path, video_store_path):

    log.debug('Trying to open video {}'.format(video_path))
    cap = cv2.VideoCapture(video_path)
    fourcc = cap.get(cv2.CAP_PROP_FOURCC)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # This is the avi codec
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    # This is the mp4 codec
    _fourcc = 875967048 # cv2.VideoWrite_fourcc(*'H264')
    out = cv2.VideoWriter(video_store_path, _fourcc, fps, (640, 480))

    if not(cap.isOpened()):
        log.debug("Cannot open video path {}".format(video_path))
        raise Exception('Cannot open video')
        return

    CWD_PATH = os.path.join(os.getenv('FACEREC_APP_DIR', '..'), 'aat')

    # Path to frozen detection graph. This is the actual model that is used for the object detection.
    MODEL_NAME = 'ssd_mobilenet_v1_coco_2017_11_17'
    PATH_TO_CKPT = os.path.join(CWD_PATH, 'object_detection', MODEL_NAME, 'frozen_inference_graph.pb')

    # List of the strings that is used to add correct label for each box.
    PATH_TO_LABELS = os.path.join(CWD_PATH, 'object_detection', 'data', 'mscoco_label_map.pbtxt')

    NUM_CLASSES = 90

    # Loading label map
    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    categories = label_map_util.convert_label_map_to_categories(label_map,
                                                                max_num_classes=NUM_CLASSES,
                                                                use_display_name=True)
    category_index = label_map_util.create_category_index(categories)

    detection_time = 0
    objects = dict()
    log.debug('Object detection with tensorflow')
    log.debug('Start reading and writing frames')
    try:
        while(cap.isOpened()):
            ret_grab = cap.grab()
            if not ret_grab:
                with open(os.path.join(settings.MEDIA_ROOT,
                                       'timelapse.log'), 'a') as f:
                    f.write('---TensorFlow Detection time---\n')
                    f.write('%r() %2.2f sec\n' % ('for all frames run detectMultiScale',  detection_time))
                break

            if (int(cap.get(1)) % 10 != 0):
                continue
            # Decode the current frame
            ret, frame = cap.retrieve()

            # optional implementation to use all/selected haar cascades
            det_start = time.time()

            # frame_with_objects = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_with_objects = frame.copy()
            detection_graph = tf.Graph()
            with detection_graph.as_default():
                od_graph_def = tf.GraphDef()
                with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
                    serialized_graph = fid.read()
                    od_graph_def.ParseFromString(serialized_graph)
                    tf.import_graph_def(od_graph_def, name='')

                sess = tf.Session(graph=detection_graph)

             # Expand dimensions since the model expects images to have shape:
             # [1, None, None, 3]
            frame_expanded = np.expand_dims(frame_with_objects, axis=0)
            frame_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

            # Each box represents a part of the image where a
            # particular object was detected.
            boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

            # Each score represent how level of confidence for each of the objects.
            # Score is shown on the result image, together with the class label.
            scores = detection_graph.get_tensor_by_name('detection_scores:0')
            classes = detection_graph.get_tensor_by_name('detection_classes:0')
            num_detections = detection_graph.get_tensor_by_name('num_detections:0')

            # Actual detection
            (boxes, scores, classes, num_detections) = sess.run(
                [boxes, scores, classes, num_detections],
                feed_dict={frame_tensor: frame_expanded})

            #log.debug("Class: {} and score: {}".format(classes, scores))
            # Visualization of the results
            vis_util.visualize_boxes_and_labels_on_image_array(
                frame_with_objects,
                np.squeeze(boxes),
                np.squeeze(classes).astype(np.int32),
                np.squeeze(scores),
                category_index,
                use_normalized_coordinates=True,
                line_thickness=8)

            # Keep annotation results
            if (len(scores[0]) > 0):
                objects[cap.get(1)] = []
            for i in range(len(scores[0])):
                if(scores[0][i] > 0.49):
                    tuple = (boxes[0][i].tolist(), classes[0][i], scores[0][i])
                    objects[cap.get(1)].append(tuple)
            # log.debug("Objects: {}".format(objects))
            log.debug("Type of 1.0:".format(type(classes[0][1])))

            det_end = time.time()
            detection_time += det_end - det_start

            # Write frame to video file
            try:
                log.debug("Write frame")
                out.write(cv2.resize(frame_with_objects, (640, 480)))
            except Exception as e:
                log.error("Cannot write new frame to video")
                log.error(str(e))

    except Exception as e:
        log.error(str(e))
        out.release()
        cap.release()
        return

    log.debug("Finished TF detection")
    log.debug(objects)
    out.release()
    cap.release()
    return objects


@shared_task(bind=True)
def transcribe(self, video_path):
    log.debug("Start transcribing video")

    cmd = ['autosub',  video_path]
    stdout = exec_cmd(cmd)
    srt_path = video_path[:-4] + '.srt'
    log.debug("Created SRT path: {}".format(srt_path))

    # shutil.rmtree(frames_temp_path)
    # cmd = ['ffmpeg', '-i', video_path, '-i', srt_path,
           #'-c', 'copy', '-c:s', 'mov_text', video_path]
    # stdout = exec_cmd(cmd)

    return srt_path
