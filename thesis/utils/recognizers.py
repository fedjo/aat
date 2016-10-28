import sys


class recognizer():

    def train()
        self.recognizer.train(self.faces_db, numpy.array(self.labels))

    def predictFaces(self, org_img, frames):
            gray_frame = cv2.cvtColor(org_img, cv2.COLOR_BGR2GRAY)
            for (x,y,w,h) in frames:
                nbr_pred, conf = self.recognizer.predict(gray_frame[y: y+h, x: x+w])
                print "{} is Recognized with confidence {}".format(self.face_labelsDict[nbr_pred], conf)

class LBPHRecognizer(recognizer):

    def __init__(self, faces_db, labels):
        self.recognizer = cv2.face.createLBPHFaceRecognizer()
        self.faces_db = faces_db
        self.labels = labels

class fisherFaceRecognizer(recognizer):

    def __init__(self, faces_db, labels):
        self.recognizer = cv2.face.createFisherFaceRecognizer()
        self.faces_db = faces_db
        self.labels = labels

class eigenFaceRecognizer(recognizer):

    def __init__(self, faces_db, labels):
        self.recognizer = cv2.face.createEigenFaceRecognizer()
        self.faces_db = faces_db
        self.labels = labels

class customFaceRecognizer(recognizer, FaceRecognizer):

    # This should be a C++ Mat
    labels = []
    # This should be a vector<Mat>
    histograms = [] 

    def __init__(self, faces_db, labels, 
            grid_x = 8, grid_x = 8, radius = 1, neighbors = 8, 
            threshold = sys.float_info.max, numOfClasses):

        #self.recognizer = cv2.face.createEigenFaceRecognizer()
        self.faces_db = faces_db
        self.labels = labels

        self.grid_x = grid_x
        self.grid_y = grid_y
        self.radius = radius
        self.neighbors = neighbors
        self.threshold = threshold
        self.classes = numOfClasses

    
