FROM opencv

ADD project /project

RUN cp /lib/lib/python2.7/dist-packages/cv2.so /usr/lib/python2.7/dist-packages

RUN pip install -r /project/requirements.txt

WORKDIR /project
