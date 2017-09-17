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
    pkg-config \
    sqlite3

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

# Add source code of OpenCV
COPY opencv/ /facerec/opencv

# Add source code of OpenCV contrib
COPY opencv_contrib /facerec/opencv_contrib

# Switch working directory to source code.
WORKDIR /facerec

# Build and install OpenCV
RUN cd opencv && \
    mkdir build && \
    cd build && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE \
#    -D CMAKE_INSTALL_PREFIX=/lib \
    -D PYTHON2_EXECUTABLE=/usr/bin/python2.7 \
    -D PYTHON_INCLUDE_DIR=/usr/include/python2.7 \
    -D \
PYTHON2_NUMPY_INCLUDE_DIRS=/usr/local/lib/python2.7/dist-packages/numpy/core/include \
    -D INSTALL_C_EXAMPLES=OFF \
    -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D OPENCV_EXTRA_MODULES_PATH=/facerec/opencv_contrib/modules \
    -D BUILD_EXAMPLES=OFF .. && \
    make -j8

RUN cd opencv/build && \
    make install && \
    ldconfig

RUN cp /usr/local/lib/python2.7/dist-packages/cv2.so /usr/lib/python2.7/dist-packages

# Add source code of opencv_dnn
ADD opencv_dnn /facerec/opencv_dnn

WORKDIR /facerec/opencv_dnn

RUN make

ENV PATH=/facerec/opencv_dnn:${PATH}

ENV LD_LIBRARY_PATH=/usr/local/lib

# Install ffmpeg
RUN apt-get install -y software-properties-common python-software-properties && \
    add-apt-repository -y ppa:mc3man/trusty-media && \
    apt-get update && \
    apt-get install -y \
    ffmpeg

