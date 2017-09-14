import sys
import os
import cv2
import numpy
import logging
from json import JSONEncoder

from django.conf import settings


log = logging.getLogger(__name__)


class Recognizer(object):

    def __init__(self, recongnName):
        # Dictionary providing the recognizer class for each recognizer
        self.recognDict = {
                    'LBPH': cv2.face.createLBPHFaceRecognizer,
                    'FF':  cv2.face.createFisherFaceRecognizer,
                    'EF': cv2.face.createEigenFaceRecognizer,
                    'KNN': cv2.face.createLBPHFaceRecognizer
                }
        self.recongnName = recongnName
        self.recognizer = self.recognDict[recongnName]()

    def train(self, faces_db, labels):
        if os.path.isfile('rec-' + self.recongnName + '.yml'):
            self.recognizer.load('rec-' + self.recongnName + '.yml')
            return
        try:
            self.recognizer.train(faces_db, numpy.array(labels))
            self.recognizer.save('rec-' + self.recongnName + '.yml')
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
                gray_resized = cv2.resize(gray_img[y: y+h, x: x+w], (80, 80))
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
