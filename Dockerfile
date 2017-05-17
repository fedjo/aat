FROM opencv

ADD requirements.txt /tmp

RUN pip install -r /tmp/requirements.txt

RUN cp /lib/lib/python2.7/dist-packages/cv2.so /usr/lib/python2.7/dist-packages

ADD project /project

WORKDIR /project

RUN mv static/Flat-UI static/flat-ui
