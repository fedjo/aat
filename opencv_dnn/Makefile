CXX=g++

INCLUDES = -I/lib/include
LIBPATHS = -L/lib/lib
LIBRARIES = -lopencv_core -lopencv_dnn -lopencv_ximgproc -lopencv_imgproc \
	    -lopencv_face -lopencv_imgcodecs -lopencv_highgui

OBJDETECT = objdetect
SELECTIVESEARCH = selectivesearch

all: $(SELECTIVESEARCH) $(OBJDETECT)

$(OBJDETECT): caffe_googlenet.cpp
	$(CXX) $(INCLUDES) $(LIBPATHS) -o $@ $< $(LIBRARIES)

$(SELECTIVESEARCH): selectivesearchsegmentation.cpp
	$(CXX) $(INCLUDES) $(LIBPATHS) -o $@ $< $(LIBRARIES)

clean:
	rm -f *.o $(SELECTIVESEARCH) $(OBJDETECT)


