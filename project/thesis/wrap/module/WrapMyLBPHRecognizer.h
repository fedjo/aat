struct py_Mat;
typedef struct py_Mat py_Mat;

struct py_MyLBPHRecognizer;
typedef struct py_MyLBPHRecognizer py_MyLBPHRecognizer;

py_Mat* py_MatCreate(int rows, int cols, int type, void* data);
void py_MatDestroy(py_Mat *mat);

py_MyLBPHRecognizer* py_create(int numOfClasses, int radius, int neighbors,
                                              int grid_x, int grid_y, double threshold); 
void py_destroy(py_MyLBPHRecognizer* rec);
void py_load(py_MyLBPHRecognizer* rec, const char* filename);
void py_predict(py_MyLBPHRecognizer* rec, py_Mat* mat, int useThreshold, int neighbors, int *label);

