from django.conf import settings
from django.core.files.uploadedfile import TemporaryUploadedFile
from recognizer_utils import Recognizer

import os
import cv2
import logging

from thesis.models import Cascade
from thesis.utils.general_utils import create_csv_file, read_csv_file


log = logging.getLogger(__name__)


# Function to train and get the recognizer
def configure_recognizer(name, faces_path, size=(0, 0)):
    # Read CSV face file and populate Face training set and labels
    frontal_cascade = Cascade.objects.get(pk=1)
    cv_frontal_cascade = cv2.CascadeClassifier(frontal_cascade.xml_file.path)
    csv_path = create_csv_file(faces_path)
    if name != 'LBPH':
        size = (160, 120)
    (face_labelsDict, faces_db, labels) = read_csv_file(name, csv_path,
                                                        cv_frontal_cascade,
                                                        size)
    myrecognizer = Recognizer(name, size)
    myrecognizer.train(faces_db, labels)
    return (myrecognizer, face_labelsDict)


# Function to return the full path where the 
# annotated video will be saved
def create_annotated_video_path(filename, recognizer_name):
    if not recognizer_name:
        recognizer_name = 'NO_FACE_RECOGNITION'

    if isinstance(filename, TemporaryUploadedFile):
        filepath = filename.temporary_file_path()
    else:
        filepath = filename

    filename = os.path.basename(filepath).split('.')[0]
    newfilename = filename + '-' + recognizer_name + '.mp4'
    log.debug("This is the annotated video name: {}".format(newfilename))
    return os.path.join(settings.CACHE_ROOT, newfilename)


#class Video

    #def __init__(self, path,
                 #cascades=['haarcascade_frontalface_alt2.xml',
                           #'haarcascade_profileface.xml',
                           #'haarcascade_frontalcatface_extended.xml',
                           #'haarcascade_frontalcatface.xml',
                           #'haarcascade_frontalface_default.xml']):
        ## Path of the video file
        #if isinstance(path, TemporaryUploadedFile):
            #self.video_path = path.temporary_file_path()
        #else:
            #self.video_path = path
        ## Face Training set of the recognizer
        #self.faces_db = []
        ## self.all_face_frames = []
        ## Array with all the labels of the people from the face db
        #self.labels = []
        ## Dictionary holding the label as a key and name of the person as value
        #self.face_labelsDict = {}
        ## Classifiers for detectMultiScale() face detector
        #self.face_cascade = cv2.CascadeClassifier(
                #os.path.join(settings.STATIC_ROOT, 'haar_cascades',
                             #'haarcascade_frontalface_alt2.xml'))
        #self.profile_cascade = cv2.CascadeClassifier(
                #os.path.join(settings.STATIC_ROOT, 'haar_cascades',
                             #'haarcascade_profileface.xml'))

        ## optional implementation to use all/selected haar cascades
        #cascadesdir = os.path.join(settings.STATIC_ROOT, 'haar_cascades')
        #self.haarcascades = [cv2.CascadeClassifier(
            #os.path.join(cascadesdir, x))
            #for x in os.listdir(cascadesdir) if x in cascades]

        
