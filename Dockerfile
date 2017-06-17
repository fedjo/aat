FROM opencv

RUN apt-get update && apt-get install -y sqlite3

ADD requirements.txt /tmp

RUN pip install -r /tmp/requirements.txt

RUN cp /lib/lib/python2.7/dist-packages/cv2.so /usr/lib/python2.7/dist-packages

ADD opencv_dnn /opencv_dnn

WORKDIR /opencv_dnn

RUN make

ENV PATH=/opencv_dnn:${PATH}

ENV LD_LIBRARY_PATH=/lib/lib

ADD project /opt/project

WORKDIR /opt/project

RUN mv static/Flat-UI static/flat-ui
