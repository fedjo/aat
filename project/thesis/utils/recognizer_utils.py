import sys
import os
import cv2
import numpy
import logging
from json import JSONEncoder

from django.conf import settings


log = logging.getLogger(__name__)


class Recognizer(object):

    def __init__(self, recongnName, size):
        # Dictionary providing the recognizer class for each recognizer
        self.recognDict = {
                    'LBPH': cv2.face.createLBPHFaceRecognizer,
                    'FF':  cv2.face.createFisherFaceRecognizer,
                    'EF': cv2.face.createEigenFaceRecognizer,
                    'KNN': cv2.face.createLBPHFaceRecognizer
                }
        self.recongnName = recongnName
        self.recognizer = self.recognDict[recongnName]()
        self.train_data_dir = os.path.join(settings.MEDIA_ROOT,
                                           'recognizer_train_data')
        self.size = size

    def train(self, faces_db, labels):
        pretrained_filepath = os.path.join(self.train_data_dir,
                                           'rec-' + self.recongnName +
                                           '-' + str(self.size[0]) + 'x' +
                                           str(self.size[1]) + '.yml')
        if self.recongnName == 'LBPH':
            pretrained_filepath = os.path.join(self.train_data_dir,
                                               'mecanex_LBPHfaces_model_5.yml')
        if os.path.exists(pretrained_filepath):
            log.debug("Loading existing pretrained file: {}"
                      .format(pretrained_filepath))
            self.recognizer.load(pretrained_filepath)
            return
        try:
            log.debug("Creating trained file: {}"
                      .format(pretrained_filepath))
            self.recognizer.train(faces_db, numpy.array(labels))
            self.recognizer.save(pretrained_filepath)
        except Exception as e:
            log.error('error: ', str(e))
        finally:
            return

    def predictFaces(self, gray_img, (x, y, w, h), labelsDict):
        with open(os.path.join('/tmp', 'faces_in_current_video.txt'),
                  'a+') as f:
            # gray_frame = cv2.cvtColor(org_img, cv2.COLOR_BGR2GRAY)
            # for (x,y,w,h) in frames:
            conf = 0.0
            if (self.recongnName is not 'LBPH') and (self.recongnName is not 'KNN'):
                # Eigen/Fisher face recognizer
                gray_resized = cv2.resize(gray_img[y: y+h, x: x+w], self.size)
                nbr_pred, conf = self.recognizer.predict(gray_resized)
            elif self.recognizer is 'KNN':
                # KNN-LBPH recognizer
                nbr_pred, conf = self.recognizer.predict_knn(
                        gray_img[y: y+h, x: x+w], 15, True, 5)
            else:
                # LBPH recognizer
                nbr_pred, conf = self.recognizer.predict(gray_img[y:y+h, x:x+w])
            #log.debug("{} is Recognized with confidence  {}"
                      #.format(labelsDict[nbr_pred], conf))
            if (
                (self.recongnName == 'LBPH' and conf <= 160.5) or
                (self.recongnName == 'FF' and conf <= 420) or
                (self.recongnName == 'EF' and conf <= 2100)
               ):
                f.write(labelsDict[nbr_pred] + '\n')
        return (labelsDict[nbr_pred], conf)
