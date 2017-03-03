#! /bin/bash

sudo make install
sudo ldconfig

cd ~/.virtualenvs/cv3/lib/python2.7/site-packages/
ln -s /usr/local/lib/python2.7/dist-packages/cv2.so cv2.so
