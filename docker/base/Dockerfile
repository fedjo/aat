FROM ubuntu:trusty

RUN apt-get update && apt-get install --fix-missing -y \
    python \
    gcc \
    apt-utils \
    python-dev \
    python-pip \
    build-essential \
    cmake \
    libffi6 \
    pkg-config

RUN apt-get install -y \
    libjpeg8-dev \
    libtiff4-dev \
    libjasper-dev \
    libpng12-dev

RUN apt-get install -y \
    libgtk2.0-dev

RUN apt-get install -y \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev

RUN pip install numpy 
    #django \
    #cffi \
    #virtualenv \
    #virtualenvwrapper \
    #numpy

#RUN export WORKON_HOME=$HOME/.virtualenvs && \
    #source /usr/local/bin/virtualenvwrapper.sh

#RUN mkvirtualenv cv3

ADD opencv/ /opt/opencv

ADD opencv_contrib/ /opt/opencv_contrib

WORKDIR /opt/


RUN cd opencv && \
    mkdir build && \
    cd build && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/lib \
    -D PYTHON2_EXECUTABLE=/usr/bin/python2.7 \
    -D PYTHON_INCLUDE_DIR=/usr/include/python2.7 \
    -D \
PYTHON2_NUMPY_INCLUDE_DIRS=/usr/local/lib/python2.7/dist-packages/numpy/core/include \
    -D INSTALL_C_EXAMPLES=OFF \
    -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D OPENCV_EXTRA_MODULES_PATH=/opt/opencv_contrib/modules \
    -D BUILD_EXAMPLES=OFF .. && \
    make -j8

RUN cd opencv/build && \
    make install && \
    ldconfig

#ADD . /thesis/

#WORKDIR /thesis/
