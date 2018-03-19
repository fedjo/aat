import sys
import os
import cv2
import numpy
import logging
import json

from django.conf import settings
from django.core.files import File

from aat.models import Cascade, RecognizerPreTrainedData
from aat.utils.utils import create_csv_file, read_csv_file

log = logging.getLogger(__name__)


def create_recognizer(type):
    recognizers = {
                'LBPH': cv2.face.LBPHFaceRecognizer_create,
                'FF':  cv2.face.FisherFaceRecognizer_create,
                'EF': cv2.face.EigenFaceRecognizer_create,
                'KNN': cv2.face.LBPHFaceRecognizer_create
            }
    return recognizers[type]()


# Function to train and get the recognizer
# recogntype: type of recognizer LBPH, EighenFaces, FisherFaces
# facesdbname: directory of the photos of the faces
#   e.g.: SD_Faces
# facesdbpath: path to yml pretrained file
#   e.g.: /data/media/faces/SD_Faces/faces/
# size: size of the photos of the portraits of the people
def train(recogntype, facesdbname, facesdbpath, size):
    # Read CSV face file and populate Face training set and labels
    frontal_cascade = Cascade.objects.get(pk=1)
    cv_frontal_cascade = cv2.CascadeClassifier(frontal_cascade.xml_file.path)
    # CSV path e.g.: /data/media/faces/SD_Faces/faces/lala.csv
    csv_path = create_csv_file(facesdbpath)
    (face_labelsDict, npfaces, labels) = read_csv_file(recogntype, csv_path,
                                                        cv_frontal_cascade,
                                                        size)
    trained_data_path = os.path.join(settings.MEDIA_ROOT,
                                     'recognizer_train_data')
    if (recogntype == 'LBPH' or recogntype == 'KNN'):
        pretrained_filepath = os.path.join(trained_data_path,
                                       facesdbname.replace('.zip', '') +
                                       '_' + recogntype + '.yml')
    else:
        pretrained_filepath = os.path.join(trained_data_path,
                                       facesdbname.replace('.zip', '') +
                                       '_' + str(size[0]) + 'x' +
                                       str(size[1]) +
                                       '_' + recogntype + '.yml')

    recognizer = create_recognizer(recogntype)
    try:
        log.debug("Creating trained file: {}"
                  .format(pretrained_filepath))
        recognizer.train(npfaces, numpy.array(labels))
        recognizer.write(pretrained_filepath)
        # Save the YAML pretrained file to db
        prtrdata = RecognizerPreTrainedData()
        prtrdata.name = os.path.basename(pretrained_filepath)
        prtrdata.recognizer = recogntype
        with open(pretrained_filepath) as f:
            prtrdata.yml_file.save(pretrained_filepath, File(f))

        # Save a list of faces that this database recognizes
        # keeping the order of the labels
        # For example:
        # label 1 is ptrdata.faces[0]
        # label 2 is ptrdata.faces[1] etc
        tmp = ""
        for label, person in face_labelsDict.iteritems():
            tmp += "{}, ".format(person)
        prtrdata.faces = tmp[:-2]

        prtrdata.save()

    except Exception as e:
        log.error(str(e))
        raise e
        return
    return face_labelsDict


# Load a YAML file to recognizer
def load(recid):
    ptrdataqs = RecognizerPreTrainedData.objects.filter(name=recid)
    ptrdata = ptrdataqs.get()
    recognizer = create_recognizer(ptrdata.recognizer)
    recognizer.read('/' + ptrdata.yml_file.url)
    log.debug("Successfully read pretrained file {}!".format(ptrdata.yml_file.url))
    tmp = ptrdata.faces.split(', ')
    facelabels = dict([tmp.index(i), str(i)] for i in tmp)
    return (recognizer, facelabels)


def predictFaces(recognizer, recid, gray_img, (x, y, w, h), labelsDict, size=None):
    try:
        ptrdataqs = RecognizerPreTrainedData.objects.filter(name=recid)
        ptrdata = ptrdataqs.get()
        recogntype = ptrdata.recognizer
        with open(os.path.join('/tmp', 'faces_in_current_video.txt'),
                  'a+') as f:
            # gray_frame = cv2.cvtColor(org_img, cv2.COLOR_BGR2GRAY)
            # for (x,y,w,h) in frames:
            conf = 0.0
            if ((not recogntype == 'LBPH') and
                (not recogntype == 'KNN')):
                # Eigen/Fisher face recognizer
                log.debug('Eighen prediction:' + recogntype)
                gray_resized = cv2.resize(gray_img[y: y+h, x: x+w], size)
                nbr_pred, conf = recognizer.predict(gray_resized)
            elif (recognizer == 'KNN'):
                # KNN-LBPH recognizer
                nbr_pred, conf = recognizer.predict_knn(
                        gray_img[y: y+h, x: x+w], 15, True, 5)
            else:
                # LBPH recognizer
                nbr_pred, conf = recognizer.predict(gray_img[y:y+h, x:x+w])
                log.debug("{} is Recognized with confidence  {}"
                            .format(labelsDict[nbr_pred], conf))
            if (
                (recogntype == 'LBPH' and conf <= 160.5) or
                (recogntype == 'FF' and conf <= 420) or
                (recogntype == 'EF' and conf <= 2100)
               ):
                f.write(labelsDict[nbr_pred] + '\n')
        return (labelsDict[nbr_pred], conf)
    except Exception as e:
        log.error(str(e))
        return
