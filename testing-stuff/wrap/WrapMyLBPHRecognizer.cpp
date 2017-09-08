#include "MyLBPHRecognizer.h"

#ifdef __cplusplus
extern "C" {
#endif

    #include "WrapMyLBPHRecognizer.h"

#ifdef __cplusplus
}
#endif

#define AS_TYPE(Type, Obj) reinterpret_cast<Type *>(Obj)
#define AS_CTYPE(Type, Obj) reinterpret_cast<const Type *>(Obj)

using namespace cv;
using namespace std;

py_Mat* py_MatCreate(int rows, int cols, int type, void* data)
{
    return AS_TYPE(py_Mat, 
            new Mat(rows, cols, type, data));

}

void py_MatDestroy(py_Mat* mat)
{
    if(!mat)
        return;
    delete AS_TYPE(Mat, mat);
}

py_MyLBPHRecognizer* py_create(int numClasses, int radius, int neighbors,
                                                int grid_x, int grid_y, double threshold)
{
    return AS_TYPE(py_MyLBPHRecognizer, 
            new MyLBPHRecognizer(numClasses, radius, neighbors, grid_x, grid_y, threshold));
} 

void py_destroy(py_MyLBPHRecognizer* rec)
{
    if(!rec)
        return;
    delete AS_TYPE(MyLBPHRecognizer, rec);
}

void py_load(py_MyLBPHRecognizer* rec, const char* filename)
{
   std::string file = filename;
   FileStorage fs(file, cv::FileStorage:: READ);
   MyLBPHRecognizer* myrec = AS_TYPE(MyLBPHRecognizer, rec);
   myrec->load(fs);
        
}

void py_predict(py_MyLBPHRecognizer* rec, py_Mat* mat, int useThreshold, int neighbors, int *label)
{
    Mat* img2 = AS_TYPE(Mat, mat);
    Mat img;
	cvtColor(img, *img2, CV_BGR2GRAY);
    MyLBPHRecognizer* myrec = AS_TYPE(MyLBPHRecognizer, rec);
    bool useThres;
    if(useThreshold==1)
        useThres = true;
    else
        useThres = false;

    myrec->predict(img, useThres, neighbors, *label);
}
