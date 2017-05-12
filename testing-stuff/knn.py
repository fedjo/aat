import cv2 

img = 'img.png'

faceCascade = \
cv2.CascadeClassifier('/home/yiorgos/thesis/static/haarcascade_frontalface_alt2.xml')

image = cv2.imread(img)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
        )


print "Found {0} faces!".format(len(faces))

# Draw a rectangle around the faces
for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        rec = cv2.face.createKNNLBPHFaceRecognizer()
        rec2 = cv2.face.createLBPHFaceRecognizer()
        rec.load('../rec-LBPH.yml')
        rec2.load('../rec-LBPH.yml')

        nbbr_pred, conf= rec.predict(gray[y:y+h,x:x+w ])
        #nb = rec2.predict(gray[y:y+h,x:x+w ])
        #print nbbr_pred
        #print nb 



cv2.imshow("Faces found" ,image)
cv2.waitKey(0)



