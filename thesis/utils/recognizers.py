import sys
import os
import cv2
import numpy


class Recognizer(object):

    def __init__(self, recongnName, faces_db, labels, labelsDict):
        # Dictionary providing the recognizer class for each recognizer
        self.recognDict = { 
                    'LBPH': cv2.face.createLBPHFaceRecognizer,
                    'FF':  cv2.face.createFisherFaceRecognizer,
                    'EF': cv2.face.createEigenFaceRecognizer
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
            #gray_frame = cv2.cvtColor(org_img, cv2.COLOR_BGR2GRAY)
            #for (x,y,w,h) in frames:
            if self.recongnName is not 'LBPH':
                gray_resized = cv2.resize(gray_img[y: y+h, x: x+w], (80, 80))
                nbr_pred, conf = self.recognizer.predict(gray_resized)
            else:
                nbr_pred, conf = self.recognizer.predict(gray_img[y: y+h, x: x+w])
            print "{} is Recognized with confidence {}".format(self.labelsDict[nbr_pred], conf)


#class customFaceRecognizer(recognizer):
    
    ## This should be a C++ Mat
    #labels = []
    ## This should be a vector<Mat>
    #histograms = [] 

    #def __init__(self, faces_db, labels, 
            #grid_x = 8, grid_x = 8, radius = 1, neighbors = 8, 
            #threshold = sys.float_info.max, numOfClasses):

        ##self.recognizer = cv2.face.createEigenFaceRecognizer()
        #self.faces_db = faces_db
        #self.labels = labels

        #self.grid_x = grid_x
        #self.grid_y = grid_y
        #self.radius = radius
        #self.neighbors = neighbors
        #self.threshold = threshold
        #self.classes = numOfClasses

    #def load(filename):
        ## TODO
        ## Implement the reading functionality
		#fs = cv2.FileStorage(filename, cv2.FileStorage_READ);
        #if not fs.isOpened():
			##CV_Error(CV_StsError, "File can't be opened for writing!");
            #pass

        #self.radius = fs['radius']
        #self.neighbors = fs['neighbors']
        #self.grid_x = fs['grid_x']
        #self.grid_y = fs.['grid_y']
		## Read matrices
		##readFileNodeList(fs["histograms"], _histograms);
		#self.labels = fs['labels']

		#fs.release();

   #def save(filename):
        #fs = cv2.FileStorage(filename, cv2.FileStorage_WRITE)
        #if not fs.isOpened():
			##CV_Error(CV_StsError, "File can't be opened for writing!");
            #pass

        ## TODO
        ## Here to implement the writing funcitonality
        
        #fs.realease()

    ##def readFileNodeList(filenode, result):
        ##if filenode.type() cv2.FileNode_SEQ:
            ##for it in filenode:




