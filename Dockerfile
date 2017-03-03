FROM ubuntu:trusty

RUN apt-get update && apt-get install --fix-missing -y \
    python \
    gcc \
    apt-utils \ 
    python-dev \
    python-pip \
    build-essential \ 
    cmake \
    git \ 
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

RUN pip install \
    django \
    #cffi \
    virtualenv \
    virtualenvwrapper \ 
    numpy

#RUN export WORKON_HOME=$HOME/.virtualenvs && \
    #source /usr/local/bin/virtualenvwrapper.sh

#RUN mkvirtualenv cv3

WORKDIR /opt/

RUN git clone https://github.com/opencv/opencv.git && \
    cd opencv && \
    git checkout 3.2.0 

WORKDIR /opt/

RUN git clone https://github.com/opencv/opencv_contrib.git && \
    cd opencv_contrib && \
    git checkout 3.2.0 

#RUN cd opencv && \
    #mkdir build && \ 
    #cd build && \
    #cmake -D CMAKE_BUILD_TYPE=RELEASE \
    #-D CMAKE_INSTALL_PREFIX=/lib \
    #-D INSTALL_C_EXAMPLES=ON \
    #-D INSTALL_PYTHON_EXAMPLES=ON \
    #-D OPENCV_EXTRA_MODULES_PATH=/opencv_contrib/modules \
    #-D BUILD_EXAMPLES=ON .. && \
    #make -j8

#RUN make install && \
    #ldconfig

#ADD . /thesis/

#WORKDIR /thesis/
