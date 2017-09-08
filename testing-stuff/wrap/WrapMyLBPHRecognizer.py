import os
from cffi import FFI

ffi = FFI()

ffi.set_source("module._wrappedMyLBPH",
    """ // passed to the real C compiler
        #include "WrapMyLBPHRecognizer.h"
    """,
    extra_objects=['MyLBPHRecognizer.o', 'WrapMyLBPHRecognizer.o'],
    library_dirs=['/usr/local/lib'],
    libraries=['opencv_highgui', 'opencv_videoio', 'opencv_imgcodecs',
        'opencv_photo', 'opencv_imgproc', 'opencv_core', 'opencv_face',
        'opencv_latentsvm', 'opencv_objdetect'])   # or a list of libraries to link with
    # (more arguments like setup.py's Extension class:
    # include_dirs=[..], extra_objects=[..], and so on)

with open(os.path.join(os.path.dirname(__file__), "module/WrapMyLBPHRecognizer.h")) as f:
    ffi.cdef(f.read())

if __name__ == "__main__":
    ffi.compile(verbose=True)
