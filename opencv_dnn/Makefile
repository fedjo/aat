CXX=g++

LIBRARIES = -lopencv_core  -lopencv_dnn -lopencv_imgproc -lopencv_face -lopencv_imgcodecs \

OBJDETECT = objdetect

all: $(OBJDETECT)

$(OBJDETECT): caffe_googlenet.cpp
	$(CXX) -o $@ $< $(LIBRARIES)

clean:
	rm -f *.o $(OBJDETECT)


