FROM ubuntu:xenial

# Install build essentials
RUN set -x && \
    apt-get update -q && \
    apt-get install --no-install-recommends --fix-missing -yq  \
    python \
    gcc \
    apt-utils \
    python-dev \
    python-pip \
    build-essential \
    cmake \
    libffi6 \
    pkg-config \
    sqlite3 && \
    pip install --upgrade pip setuptools && \
    find / -name '*.py[co]' -delete

# Install image libs
RUN set -x && \
    apt-get install --no-install-recommends --fix-missing -yq  \
    libjpeg8-dev \
    libtiff-dev \
    libjasper-dev \
    libpng12-dev

# Install gtk
RUN set -x && \
    apt-get install --no-install-recommends --fix-missing -yq  \
    libgtk2.0-dev

# Install video libs
RUN set -x && \
    apt-get install --no-install-recommends --fix-missing -yq  \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev

# Install ffmpeg
RUN set -x && \
    apt-get install --no-install-recommends --fix-missing -yq  \
    software-properties-common python-software-properties && \
    #add-apt-repository -y ppa:mc3man/trusty-media && \
    add-apt-repository -y ppa:mc3man/xerus-media && \
    apt-get update -q && \
    apt-get install --no-install-recommends --fix-missing -yq \
    ffmpeg \
    libgstreamer1.0-dev libgstreamer0.10-dev \
    #libgstreamer-plugins-bad0.10-dev \
    libgstreamer-plugins-base0.10-dev \
    libgstreamer-plugins-bad1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-good1.0-dev \
    gstreamer0.10-plugins-good \
    #gstreamer0.10-plugins-ugly \
    gstreamer1.0-plugins-ugly &&\
    apt-get autoremove -yq && \
    apt-get clean -q && rm -rf /var/lib/apt/lists/*

# Install numpy, uwsgi
RUN pip install numpy  uwsgi && \
    find / -name '*.py[co]' -delete

# Switch working directory to source code.
WORKDIR /facerec

# Add source code of OpenCV
COPY opencv/ /facerec/opencv

# Add source code of OpenCV contrib
COPY opencv_contrib /facerec/opencv_contrib

# Build, install OpenCV
# then delete source code directories to
# eliminate space
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
    make -j8 && \
    make install && \
    ldconfig && \
    cd /facerec && \
    rm -rf opencv/ opencv_contrib/

RUN cp /usr/local/lib/python2.7/dist-packages/cv2.so /usr/lib/python2.7/dist-packages

ENV LD_LIBRARY_PATH=/usr/local/lib

# Copy tensorflow object detection module
COPY models/research/object_detection /facerec/object_detection

# Copy tensorflow slim module
COPY models/research/slim /facerec/slim

# Install protobuf compiler 3.3 and compile Protobufs
RUN set -x && \
    apt-get update -q && \
    apt-get install --no-install-recommends --fix-missing -yq  \
    unzip \
    wget && \
    mkdir /opt/protoc_3.3 && \
    cd /opt/protoc_3.3 && \
    wget https://github.com/google/protobuf/releases/download/v3.3.0/protoc-3.3.0-linux-x86_64.zip && \
    chmod 775 protoc-3.3.0-linux-x86_64.zip && \
    unzip protoc-3.3.0-linux-x86_64.zip && \
    cd /facerec && \
    /opt/protoc_3.3/bin/protoc object_detection/protos/*.proto --python_out=. && \
    rm -rf /opt/protoc_3.3 && \
    apt-get remove -y wget unzip && \
    apt-get autoremove -yq && \
    apt-get clean -q && rm -rf /var/lib/apt/lists/*


# Extend python environment
ENV PYTHONPATH=$PYTHONPATH:/facerec:/facerec/slim
