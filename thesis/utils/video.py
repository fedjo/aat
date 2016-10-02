from django.conf import settings

import numpy
import cv2
import sys
import csv


class Video:

    def __init__(self, f):
        self.f = f
        self.name = f.temporary_file_path()
        self.faces_db = []
        self.profiles = []
        #self.all_face_frames = []
        self.labels = []
        self.face_cascade = cv2.CascadeClassifier('/home/yiorgos/thesis/haarcascade_frontalface_default.xml')
        self.profile_cascade = cv2.CascadeClassifier('/home/yiorgos/thesis/haarcascade_profileface.xml')


    def printName(self):
        print "This is the video name: ", self.name
        return  str(self.name)


    def detectFaces(self):
    
        cap = cv2.VideoCapture(self.name)
        fourcc = cap.get(cv2.CAP_PROP_FOURCC)
        fps = cap.get(cv2.CAP_PROP_FPS)
        #fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter('static/images/output.mp4', int(fourcc), fps, (640, 480))
        all_face_frames = []

        if not(cap.isOpened()):
            return HttpResponse('Video not opened')
        
        while(cap.isOpened()):
            retval, frame = cap.read()
            if not frame is None: 
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                out.release()
                cap.release()
                return

            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            profiles = self.profile_cascade.detectMultiScale(gray, 1.3, 5)
            #__throw_overlapping(profiles)
            if len(faces) > 0:
                all_face_frames.extend(faces)
            if len(profiles) > 0:
                all_face_frames.extend(profiles)

            # Draw all the rectangles of possible faces on the frame 
            detected_faces_frame = frame.copy()
            for(x,y,w,h) in all_face_frames:
                cv2.rectangle(detected_faces_frame, (x,y), (x+w, y+h), (255,0,0),2)

            # Write frame to video file
            scaled_detected_faces_frame = cv2.resize(detected_faces_frame, (640, 480))
            out.write(scaled_detected_faces_frame)
            print "Frame written to file"

            # Predict possible faces on the original frame
            self.predictFaces(frame, all_face_frames)

            #cv2.namedWindow('img', cv2.WINDOW_NORMAL)
            #cv2.imshow('img', frame)
            if cv2.waitKey(20) & 0xFF == ord('q'):
                break
    
        out.release()
        cap.release()
        #cv2.waitKey(0)
        cv2.destroyAllWindows()


    def LBPHRecognizer(self):
        self.recognizer = cv2.face.createLBPHFaceRecognizer()
        self.recognizer.train(self.faces_db, numpy.array(self.labels))

    def fisherFaceRecognizer(self):
	self.recognizer = cv2.face.createFisherFaceRecognizer()
	self.recognizer.train(self.faces_db, numpy.array(self.labels))

    def eigenFaceRecognizer(self):
	self.recognizer = cv2.face.createEigenFaceRecognizer()
	self.recognizer.train(self.faces_db, numpy.array(self.labels))


    def predictFaces(self, org_img, frames):
            gray_frame = cv2.cvtColor(org_img, cv2.COLOR_BGR2GRAY)
            for (x,y,w,h) in frames:
                nbr_pred, conf = self.recognizer.predict(gray_frame[y: y+h, x: x+w])
                #print str(nbr_pred)


    def read_csv_file(self, path):
        path = settings.STATIC_PATH + "/faces.csv"
        img_path = settings.STATIC_PATH + "/"
        with open(path, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for row in reader: 
                #print img_path+str(row[0])
                image = cv2.imread(img_path + str(row[0]))
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                for (x,y,w,h) in faces: 
                    self.faces_db.append(gray[y:y+h, x:x+w])
                    self.labels.append(int(row[1]))
                   # cv2.imshow("adding image to set...", image[y:y+h, x:x+w])
                   # cv2.waitKey(30)

