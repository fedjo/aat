#include <opencv2/core.hpp>
//#include <opencv2/contrib/contrib.hpp>
#include <opencv2/face.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/objdetect/objdetect.hpp>

#include <vector>
#include <string>

using namespace std;
using namespace cv;
using namespace cv::face;

class MyLBPHRecognizer : public FaceRecognizer
{
private:
	int _grid_x;
	int _grid_y;
	int _radius;
	int _neighbors;
	double _threshold;
	int _classes;

	vector<Mat> _histograms;
	Mat _labels;
public:
	using FaceRecognizer::save;
	using FaceRecognizer::load;
	MyLBPHRecognizer(int numOfClasses, int radius_ = 1, int neighbors_ = 8,
		int gridx = 8, int gridy = 8,
		double threshold = DBL_MAX) :
		_classes(numOfClasses),
		_grid_x(gridx),
		_grid_y(gridy),
		_radius(radius_),
		_neighbors(neighbors_),
		_threshold(threshold) {}
	~MyLBPHRecognizer() { }

	// Computes a LBPH model with images in src and
	// corresponding labels in labels.
	void train(InputArrayOfArrays src, InputArray labels);

	// Predicts the label of a query image in src.
	int predict(InputArray src) const;

	// Predicts the label and confidence for a given sample.
	void predict(InputArray _src, int &label, double &dist) const;

	// KNN-BASED PREDICTION
	void predict(InputArray _src, bool useThreshold, int neighbors, int &label) const;

	// See FaceRecognizer::load.
	void load(const FileStorage& fs);

	// See FaceRecognizer::save.
	void save(FileStorage& fs) const;
};
