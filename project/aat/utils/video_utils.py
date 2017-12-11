from django.conf import settings
from django.core.files.uploadedfile import TemporaryUploadedFile
from recognizer_utils import Recognizer

import os
import cv2
import logging

from aat.models import Cascade
from aat.utils.general_utils import create_csv_file, read_csv_file


log = logging.getLogger(__name__)


# Function to train and get the recognizer
def configure_recognizer(name, dbname, faces_path, size=(160, 120)):
    # Read CSV face file and populate Face training set and labels
    frontal_cascade = Cascade.objects.get(pk=1)
    cv_frontal_cascade = cv2.CascadeClassifier(frontal_cascade.xml_file.path)
    csv_path = create_csv_file(faces_path)
    (face_labelsDict, faces_db, labels) = read_csv_file(name, csv_path,
                                                        cv_frontal_cascade,
                                                        size)
    myrecognizer = Recognizer(name, size)
    myrecognizer.train(faces_db, labels, dbname)
    return (myrecognizer, face_labelsDict)


# Function to return the full path where the
# annotated video will be saved
def create_annotated_video_path(jsondata):

    filename = jsondata['content']['path']
    if isinstance(filename, TemporaryUploadedFile):
        filepath = filename.temporary_file_path()
    else:
        filepath = filename

    filename = os.path.basename(filepath).split('.')[0]

    newfilename = filename
    if ('cascade' in jsondata.keys()):
        newfilename += '-'
        newfilename += 'facedet'
        if 'recognizer' in jsondata.keys():
            newfilename += '-'
            newfilename += jsondata['recognizer']['name']
    if('objdetector' in jsondata.keys()):
        newfilename += '-'
        newfilename += 'objdet'
    if ('transcription' in jsondata.keys()):
        newfilename += '-'
        newfilename += 'transcibe'

    newfilename += '.mp4'
    log.debug("This is the annotated video name: {}".format(newfilename))
    return os.path.join(settings.CACHE_ROOT, newfilename)
