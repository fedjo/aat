import sys
import os
import cv2
import numpy
import logging
import json

from django.conf import settings
from django.core.files import File

from thesis.models import RecognizerPreTrainedData

log = logging.getLogger(__name__)


class Recognizer(object):

    def __init__(self, rec_name, size):
        # Dictionary providing the recognizer class for each recognizer
        self.recognDict = {
                    'LBPH': cv2.face.LBPHFaceRecognizer_create,
                    'FF':  cv2.face.FisherFaceRecognizer_create,
                    'EF': cv2.face.EigenFaceRecognizer_create,
                    'KNN': cv2.face.LBPHFaceRecognizer_create
                }
        self.rec_name = rec_name
        self.recognizer = self.recognDict[rec_name]()
        self.train_data_dir = os.path.join(settings.MEDIA_ROOT,
                                           'recognizer_train_data')
        if rec_name == 'LBPH':
            size = ('', '')
        self.size = size

    def train(self, faces_db, labels, dbname=''):
        pretrained_filepath = os.path.join(self.train_data_dir,
                                           'rec-' + self.rec_name +
                                           '-' + dbname +
                                           '-' + str(self.size[0]) + 'x' +
                                           str(self.size[1]) + '.yml')
        #if self.rec_name == 'LBPH':
            # pretrained_filepath = os.path.join(self.train_data_dir,
            #                                   'mecanex_LBPHfaces_model_5.yml')
            #pretrained_filepath = os.path.join(self.train_data_dir,
            #                                   'mecanex_LBPHfaces_plus_Tajani.yml')
        if os.path.exists(pretrained_filepath):
            log.debug("Loading existing pretrained file: {}"
                      .format(pretrained_filepath))
            self.recognizer.read(pretrained_filepath)
            return
        try:
            log.debug("Creating trained file: {}"
                      .format(pretrained_filepath))
            self.recognizer.train(faces_db, numpy.array(labels))
            self.recognizer.write(pretrained_filepath)
            # Save the YAML pretrained file to db
            # TODO
            # Save names of faces to the db
            prtrdata = RecognizerPreTrainedData()
            prtrdata.name = os.path.basename(pretrained_filepath)
            prtrdata.recognizer = self.rec_name
            with open(pretrained_filepath) as f:
                prtrdata.yml_file.save(pretrained_filepath, File(f))
            prtrdata.save()

        except Exception as e:
            log.error(e)
        finally:
            return


    def load(pretrained_path):
        self.recognizer.read(pretrained_path)


    def predictFaces(self, gray_img, (x, y, w, h), labelsDict):
        with open(os.path.join('/tmp', 'faces_in_current_video.txt'),
                  'a+') as f:
            # gray_frame = cv2.cvtColor(org_img, cv2.COLOR_BGR2GRAY)
            # for (x,y,w,h) in frames:
            conf = 0.0
            if ((not self.rec_name == 'LBPH') and
                (not self.rec_name == 'KNN')):
                # Eigen/Fisher face recognizer
                log.debug('Eighen prediction:' + self.rec_name)
                gray_resized = cv2.resize(gray_img[y: y+h, x: x+w], self.size)
                nbr_pred, conf = self.recognizer.predict(gray_resized)
            elif (self.recognizer == 'KNN'):
                # KNN-LBPH recognizer
                nbr_pred, conf = self.recognizer.predict_knn(
                        gray_img[y: y+h, x: x+w], 15, True, 5)
            else:
                # LBPH recognizer
                nbr_pred, conf = self.recognizer.predict(gray_img[y:y+h, x:x+w])
            #log.debug("{} is Recognized with confidence  {}"
                      #.format(labelsDict[nbr_pred], conf))
            if (
                (self.rec_name == 'LBPH' and conf <= 160.5) or
                (self.rec_name == 'FF' and conf <= 420) or
                (self.rec_name == 'EF' and conf <= 2100)
               ):
                f.write(labelsDict[nbr_pred] + '\n')
        return (labelsDict[nbr_pred], conf)
