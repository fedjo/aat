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
import requests
import json

# Tensorflow imports
import numpy as np
import tensorflow as tf
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
# ##################

from django.conf import settings

from aat import _detection_graph, CWD_PATH
from .models import Cascade
from .utils.utils import exec_cmd
import aat.utils.recognizer_utils as recognizer


log = logging.getLogger(__name__)


@shared_task(bind=True)
def face_detection_recognition(self, video_path, recid, haarcascades, scale,
                               neighbors, minx, miny, has_bounding_boxes,
                               framerate):

    log.debug('Trying to open video {}'.format(video_path))
    cap = cv2.VideoCapture(video_path)
    fourcc = cap.get(cv2.CAP_PROP_FOURCC)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    #out = cv2.VideoWriter(video_store_path, int(fourcc), fps, (640, 480))
    #_fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    _fourcc = 875967048 #cv2.cv.CV_FOURCC(*'MP4V')

    if not(cap.isOpened()):
        log.debug("Cannot open video path {}".format(video_path))
        return {'fd_error': 'Cannot open video'}

    try:
        if recid:
            (myrecognizer, face_labelsDict) = recognizer.load(recid)
            log.debug("Face labels dict: {}".format(face_labelsDict))

        log.debug('Start reading and writing frames')
        allface_positions = []
        while(cap.isOpened()):
            ret_grab = cap.grab()
            if not ret_grab:
                break

            # Skip frame
            if (int(cap.get(1)) % framerate != 0):
                continue

            log.debug("Read frame: {}".format(int(cap.get(1))))
            # Decode the current frame
            ret, frame = cap.retrieve()

            # Get the current frame in grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Faces Mat discovered at the current frame
            current_faces = []

            # optional implementation to use all/selected haar cascades
            db_haarcascades = Cascade.objects.filter(pk__in=haarcascades).all()
            for c in db_haarcascades:
                cascade = cv2.CascadeClassifier(c.xml_file.path)
                current_faces.extend(cascade.detectMultiScale(gray, scaleFactor=float(scale),
                                                 minNeighbors=int(neighbors),
                                                 minSize=(int(minx), int(miny))))

            # __throw_overlapping(profiles)

            if (not has_bounding_boxes and not recid):
                allface_positions += [ { 'position': {'xaxis': str(a[0]), 'yaxis': str(a[1])},
                                         'dimensions': {'width': str(a[2]), 'height': str(a[3])},
                                         'frame': str(cap.get(1)),
                                         'timecode': "{0:.2f}".format(cap.get(1)/fps) } for a in current_faces ]
                continue

            # Get copy of the current colored frame and
            # draw all the rectangles of possible faces on the frame
            # along with the name recognized
            for (x, y, w, h) in current_faces:
                facename_prob = 'person - NaN'

                value = dict()
                value['frame'] = str(cap.get(1))
                value['timecode'] = "{0:.2f}".format(cap.get(1)/fps)

                if recid:
                    # Predict possible faces on the original frame
                    (facename, prob) = recognizer.predictFaces(myrecognizer, recid, gray,
                                                    (x, y, w, h), face_labelsDict)
                    if not facename:
                        facename_prob = 'person - NaN'
                    else:
                        value['face'] = facename
                        value['probability'] = "{0:.2f}".format(prob)

                if has_bounding_boxes:
                    value['position'] = {'xaxis': str(x), 'yaxis': str(y)}
                    value['dimensions'] = {'width': str(w), 'height': str(h)}


                allface_positions.append(value)


    except Exception as e:
        log.error("Unexpected error!")
        log.error(str(e))
        return {'fd_error': str(e)}

    cap.release()

    return {'facedetection': allface_positions}


@shared_task(bind=True)
def object_detection2(self, video_path, framerate):

    log.debug('Trying to open video {}'.format(video_path))
    cap = cv2.VideoCapture(video_path)
    fourcc = cap.get(cv2.CAP_PROP_FOURCC)
    fps = cap.get(cv2.CAP_PROP_FPS)
    # This is the avi codec
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')
    # This is the mp4 codec

    if not(cap.isOpened()):
        log.debug("Cannot open video path {}".format(video_path))
        return {'od_error': 'Cannot open video'}

    # List of the strings that is used to add correct label for each box.
    PATH_TO_LABELS = os.path.join(CWD_PATH, 'object_detection', 'data', 'mscoco_label_map.pbtxt')
    # PATH_TO_LABELS = os.path.join(CWD_PATH, 'object_detection', 'data', ' oid_bbox_trainable_label_map.pbtxt')

    NUM_CLASSES = 90
    # NUM_CLASSES = 545

    # Loading label map
    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    categories = label_map_util.convert_label_map_to_categories(label_map,
                                                                max_num_classes=NUM_CLASSES,
                                                                use_display_name=True)
    category_index = label_map_util.create_category_index(categories)

    objects = []
    log.debug('Object detection with tensorflow')
    log.debug('Start reading and writing frames')
    try:
        while(cap.isOpened()):
            ret_grab = cap.grab()
            if not ret_grab:
                break

            # Skip frame
            if (int(cap.get(1)) % framerate != 0):
                continue

            log.debug("Read frame: {}".format(int(cap.get(1))))
            # Decode the current frame
            ret, frame = cap.retrieve()
            # Frame height, width
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)

            # frame_with_objects = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_with_objects = frame.copy()

            detection_graph = _detection_graph
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
            for i in range(len(scores[0])):
                if(scores[0][i] > 0.49):
                    data = dict()
                    xmin = boxes[0][i].item(1) * width
                    ymin = boxes[0][i].item(0) * height
                    rec_width = boxes[0][i].item(3) * width - xmin
                    rec_height = boxes[0][i].item(2) * height - ymin
                    data['position'] = {'xaxis': xmin, 'yaxis': ymin}
                    data['dimensions'] = {'width': rec_width, 'height': rec_height}
                    data['class'] = category_index[int(classes[0][i])]['name']
                    data['probability'] = str(scores[0][i])
                    data['frame'] = str(cap.get(1))
                    data['timecode'] = "{0:.2f}".format(cap.get(1) / fps)
                    objects.append(data)

    except Exception as e:
        log.error(str(e))
        cap.release()
        return {'od_error': str(e)}

    log.debug("Finished TF detection")
    cap.release()
    return {'objectdetection': objects}


@shared_task(bind=True)
def transcribe(self, video_path, inlang, outlang, instanceurl):
    log.debug("Start transcribing video")
    import ntpath

    srtpath = os.path.join(settings.STATIC_ROOT,
                           ntpath.basename(video_path).split('.')[0] + '.srt')
    cmd = ['autosub', '-S', inlang, '-D', outlang, '-C 4',
           '-o', srtpath, video_path]
    try:
        stdout = exec_cmd(cmd)
        log.debug("Created SRT path: {}".format(srtpath))
    except Exception as e:
        log.error(str(e))
        return {'tr_error': str(e)}

    # shutil.rmtree(frames_temp_path)
    # cmd = ['ffmpeg', '-i', video_path, '-i', srt_path,
           #'-c', 'copy', '-c:s', 'mov_text', video_path]
    # stdout = exec_cmd(cmd)

    return {'transcription': ntpath.basename(srtpath)}


@shared_task(bind=True)
def senddata(self, annotations, id=None, manual_tags=None):

    json = dict()
    json['entity-type'] = 'document'
    json['properties'] = {}
    json['properties']['ann:Annotation'] = {}


    if (not isinstance(annotations, list)):
        _annotations = [ annotations ]
    else:
        _annotations = annotations

    flatten = lambda l: [item for sublist in l for item in sublist]
    if ('error' in [x[3:] for x in flatten([a.keys() for a in _annotations])]):
        log.debug("Error to MCSSR!")
        json['properties']['ann:Annotation']['annotationStatus'] = 'FAILURE'
    else:
        log.debug("Annotations to MCSSR!")
        json['properties']['ann:Annotation']['annotationStatus'] = 'ANNOTATED'

        [json['properties']['ann:Annotation'].update(i) for i in annotations]
        if (manual_tags and isinstance(manual_tags, dict)):
            json['properties']['ann:Annotation']['manual_tags'] = manual_tags


    log.debug("Sending data to external API")
    log.debug(json)

    host = settings.EXT_SERVICE + id
    host = settings.EXT_SERVICE
    headers = {'Content-type': 'application/json',
               'Authorization': 'Basic ' + settings.EXT_BASIC_AUTH}

    req = requests.Request('PUT', host, headers=headers, json=json)
    prepared = req.prepare()
    log.debug('{}\n{}\n{}\n\n{}'.format(
        '-----------START-----------',
        prepared.method + ' ' + prepared.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in prepared.headers.items()),
        prepared.body,
    ))
    s = requests.Session()
    resp = s.send(prepared)
    if (resp.status_code == 200):
        log.debug("Sending to MCSSR succeeded!")
    else:
        log.debug("Sending to MCSSR failed!")
    log.debug(resp.text)



@shared_task(bind=True)
def returnvalues(self, annotations_list, video_path=None):

    # Process annotations_list
    # Retrive annotation process info
    # Convert to dict
    tempjson = dict()
    json = dict()
    if(isinstance(annotations_list, list)):
        [tempjson.update(i) for i in annotations_list]
    else:
        tempjson = annotations_list
    for (k, v) in tempjson.iteritems():
        if(k == 'transcription'):
            json[k] = v
            continue
        newvalue = dict()
        for elem in v:
            if (not elem['frame'] in newvalue):
                newvalue[elem['frame']] = []
                newvalue[elem['frame']].append(elem)
            else:
                newvalue[elem['frame']].append(elem)
        json[k] = newvalue

    task_list = []
    # Name of the annotated video file
    import ntpath
    filename = ntpath.basename(video_path)
    annotfilename = os.path.basename(filename).split('.')[0]
    # Add suffix
    annotfilename += '_'
    if ('facedetection' in json.keys()):
        task_list.append('facedetection')
        annotfilename += 'F'
        #if face' in json['facedetection'][0].keys():
        #    annotfilename += 'R'
        #else:
        #    annotfilename += 'D'
    if('objectdetection' in json.keys()):
        task_list.append('objectdetection')
        annotfilename += 'O'
    if ('transcription' in json.keys()):
        annotfilename += 'T'
    annotfilename += '.mp4'
    log.debug("This is the annotated video name: {}".format(annotfilename))
    s3dir = os.getenv('FACEREC_S3_DIR', '/data/s3/')
    annotfilepath = os.path.join(s3dir, 'Annotated_Videos', annotfilename)
    static_annot_symlink = os.path.join(settings.STATIC_ROOT, annotfilename)
    if (os.path.islink(static_annot_symlink)):
        os.remove(static_annot_symlink)
    os.symlink(annotfilepath, static_annot_symlink)

    # Here we construct the video with the annotations
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    _fourcc = 875967048 #cv2.cv.CV_FOURCC(*'MP4V')
    out = cv2.VideoWriter(annotfilepath, _fourcc, fps, (640, 480))

    #log.debug(json)
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret:
            fidx = cap.get(1)
            for task in task_list:
                if str(fidx) in json[task].keys():
                    for e in json[task][str(fidx)]:
                        x = int(e['position']['xaxis'])
                        y = int(e['position']['yaxis'])
                        w = int(e['dimensions']['width'])
                        h = int(e['dimensions']['height'])
                        if (task=='objectdetection'):
                            _class = e['class']
                            prob = e['probability']
                        else:
                            if 'face' in e.keys():
                                _class = e['face']
                                prob = e['probability']
                            else:
                                _class = 'person'
                                prob = "0"
                        facename_prob = _class + '-' + prob + '%'
                        # Draw rectangle around the face
                        cv2.rectangle(frame, (x, y), (x+w, y+h),
                                      (0, 0, 255), 4)
                        size = cv2.getTextSize(facename_prob, cv2.FONT_HERSHEY_PLAIN, 1.0, 1)[0]
                        cv2.rectangle(frame, (x, y-size[1]-3),
                                      (x+size[0]+4, y+3), (0, 0, 255), -1)
                        cv2.putText(frame, facename_prob, (x, y-2),
                        cv2.FONT_HERSHEY_PLAIN, 1.0, (255, 255, 255), 1)

            # Write frame to video file
            try:
                out.write(cv2.resize(frame, (640, 480)))
            except Exception as e:
                log.error("Cannot write new frame to video")
                log.error(str(e))
        else:
            break

    cap.release()
    out.release()
    tempjson['annotvideopath'] = annotfilepath

    log.debug("Returning values to UI")
    return tempjson
