import os
import csv
import cv2
import logging
import requests
import subprocess
from subprocess import PIPE

from django.conf import settings
from django.core.files.uploadedfile import TemporaryUploadedFile

from aat.models import Cascade, RecognizerPreTrainedData

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
    npfaces = []
    # List containing just the label numbers
    labels = []
    with open(csv_path, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            face_labelsDict[int(row[1])] = str(row[0]).split('/')[-2:][0]
            image = cv2.imread(os.path.join(settings.STATIC_ROOT, str(row[0])))
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # TODO
            # Check if a face was found on every single image
            # or just delete this line, assuming that every image
            # has a face
            main_faces = cascade.detectMultiScale(gray, 1.1, 6)
            if len(main_faces) == 0:
                continue
            else:
                (x, y, w, h) = main_faces[0]
                labels.append(int(row[1]))
                if recogn_name == 'LBPH':
                    npfaces.append(gray[y:y+h, x:x+w])
                    # labels.append(int(row[1]))
                    # npfaces.append(cv2.resize(gray[y:y+h, x:x+w], size))
                else:
                    npfaces.append(cv2.resize(gray[y:y+h, x:x+w], size))
    log.debug("read_csv_file parameters")
    log.debug(face_labelsDict)
    log.debug("Len of npfaces: " + str(len(npfaces)))
    #log.debug("Labels: " + str(labels))
    return (face_labelsDict, npfaces, labels)


# Send request to remote machine
def httppost(url, message):
    payload = {'message': message}
    return requests.post(url, data=payload)


# Run a command
def exec_cmd(cmd):
    try:
        log.debug("The command to be executed: %s", cmd)
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        log.debug(output)
    except OSError as exc:
        raise Exception("Couldn't execute command '%s'. Error was: %s."
                        % (cmd, exc))
    except subprocess.CalledProcessError as exc:
        msg = "Command '%s' returned exit status %s." % (' '.join(exc.cmd),
                                                         exc.returncode)
        msg += " Output was:"
        msg += ("\n%s" % exc.output) if exc.output else " ''"
        raise Exception(msg)

    return output
