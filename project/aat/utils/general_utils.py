import os
import csv
import cv2
import logging
import subprocess
from subprocess import PIPE

from django.conf import settings

log = logging.getLogger(__name__)


# This is a function to help you creating a CSV file from a face
# database with a similar hierarchie:
#
#  philipp@mango:~/facerec/data/at$ tree
#  .
#  |-- README
#  |-- s1
#  |   |-- 1.pgm
#  |   |-- ...
#  |   |-- 10.pgm
#  |-- s2
#  |   |-- 1.pgm
#  |   |-- ...
#  |   |-- 10.pgm
#  ...
#  |-- s40
#  |   |-- 1.pgm
#  |   |-- ...
#  |   |-- 10.pgm
#
def create_csv_file(faces_basepath):
    SEPARATOR = ";"
    CSV_NAME = os.path.basename(os.path.normpath(faces_basepath)) + '.csv'
    CSV_PATH = os.path.join(faces_basepath, CSV_NAME)

    if os.path.isfile(CSV_PATH):
        return CSV_PATH

    with open(CSV_PATH, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=SEPARATOR)
        label = 0
        for dirname, dirnames, filenames in os.walk(faces_basepath):
            for subdirname in dirnames:
                subject_path = os.path.join(dirname, subdirname)
                for filename in os.listdir(subject_path):
                    abs_path = "%s/%s" % (subject_path, filename)
                    writer.writerow([abs_path, label])
                label = label + 1
    return CSV_PATH


def read_csv_file(recogn_name, csv_path, cascade, size):
    log.debug('CSV file {}'.format(csv_path))
    # Dict with key the label number and value the name
    # of the person
    face_labelsDict = dict()
    # List containing images (as numpy arrays) of faces
    # to train the recognizer
    faces_db = []
    # List containing jsut the label numbers
    labels = []
    with open(csv_path, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            face_labelsDict[int(row[1])] = str(row[0]).split('/')[-2:][0]
            image = cv2.imread(os.path.join(settings.STATIC_ROOT, str(row[0])))
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            main_faces = cascade.detectMultiScale(gray, 1.1, 6)
            if len(main_faces) == 0:
                continue
            else:
                (x, y, w, h) = main_faces[0]
                labels.append(int(row[1]))
                if recogn_name == 'LBPH':
                    faces_db.append(gray[y:y+h, x:x+w])
                    # labels.append(int(row[1]))
                    # faces_db.append(cv2.resize(gray[y:y+h, x:x+w], size))
                else:
                    faces_db.append(cv2.resize(gray[y:y+h, x:x+w], size))
    log.debug("read_csv_file parameters")
    log.debug(face_labelsDict)
    log.debug("Len of faces_db: " + str(len(faces_db)))
    log.debug("Labels: " + str(labels))
    return (face_labelsDict, faces_db, labels)


def create_name_dict_from_file():
    d = {}
    faces_filepath = os.path.join('/tmp', 'faces_in_current_video.txt')
    if os.path.exists(faces_filepath):
        with open(faces_filepath, 'r') as f:
            lines = f.readlines()
            for key in lines:
                if key in d:
                    d[key] += 1
                else:
                    d[key] = 1
        os.remove(os.path.join('/tmp', 'faces_in_current_video.txt'))
    return d


def exec_cmd(cmd):
    try:
        p = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        cmd.pop()
        if stdout:
            log.debug(stdout)
    except Exception as e:
        log.error("Unexpected error: {}".format(str(e)))
        raise
    return stdout

