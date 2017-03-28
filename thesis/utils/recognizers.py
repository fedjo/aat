import sys
import os
import cv2
import numpy

from django.conf import settings

class Recognizer(object):

    def __init__(self, recongnName, faces_db, labels, labelsDict):
        # Dictionary providing the recognizer class for each recognizer
        self.recognDict = { 
                    'LBPH': cv2.face.createLBPHFaceRecognizer,
                    'FF':  cv2.face.createFisherFaceRecognizer,
                    'EF': cv2.face.createEigenFaceRecognizer,
                    'KNN': cv2.face.createLBPHFaceRecognizer
                }
        self.recongnName = recongnName
        self.labelsDict = labelsDict

        self.recognizer = self.recognDict[recongnName]()
        self.train(faces_db, labels)


    def train(self, faces_db, labels):
        if os.path.isfile('rec-'+ self.recongnName +'.yml'):
            self.recognizer.load('rec-'+ self.recongnName +'.yml')
            return
        try:
            self.recognizer.train(faces_db, numpy.array(labels))
            self.recognizer.save('rec-'+ self.recongnName +'.yml' )
        except Exception, e:
            print('error: ', str(e))
        finally:
            return

    def predictFaces(self, gray_img, (x,y,w,h)):
            f = open(os.path.join(settings.STATIC_PATH, \
                'faces_in_current_video.txt'), 'a+'); 
            #gray_frame = cv2.cvtColor(org_img, cv2.COLOR_BGR2GRAY)
            #for (x,y,w,h) in frames:
            conf = 0.0
            if (self.recongnName is not 'LBPH') and (self.recongnName is not 'KNN'):
                # Eigen/Fisher face recognizer
                gray_resized = cv2.resize(gray_img[y: y+h, x: x+w], (80, 80))
                nbr_pred, conf = self.recognizer.predict(gray_resized)
            elif self.recognizer is 'KNN':
                # KNN-LBPH recognizer
                nbr_pred, conf = self.recognizer.predict_knn(gray_img[y: y+h, x: \
                    x+w], 15, True, 5)
            else:
                # LBPH recognizer
                nbr_pred, conf = self.recognizer.predict(gray_img[y:y+h, x:x+w])
            print "{} is Recognized with confidence {}".format(self.labelsDict[nbr_pred], conf)
            if ( 
                (self.recongnName == 'LBPH' and conf <= 160.5) or  
                (self.recongnName == 'FF' and conf <= 420) or 
                (self.recongnName == 'EF' and conf <= 2100)
                ):
                f.write(self.labelsDict[nbr_pred] + '\n')
                return self.labelsDict[nbr_pred]


