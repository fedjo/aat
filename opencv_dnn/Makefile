CXX=g++

INCLUDES = -I/lib/include
LIBPATHS = -L/lib/lib
LIBRARIES = -lopencv_core  -lopencv_dnn -lopencv_imgproc -lopencv_face -lopencv_imgcodecs \

OBJDETECT = objdetect

all: $(OBJDETECT)

$(OBJDETECT): caffe_googlenet.cpp
	$(CXX) $(INCLUDES) $(LIBPATHS) -o $@ $< $(LIBRARIES)

clean:
	rm -f *.o $(OBJDETECT)


