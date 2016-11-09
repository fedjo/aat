#include "MyLBPHRecognizer.h"
#include <utility>
#include <iostream>
#include <limits>

//------------------------------------------------------------------------------
// FaceRecognizer
//------------------------------------------------------------------------------
void FaceRecognizer::update(InputArrayOfArrays src, InputArray labels) {
	if (dynamic_cast<MyLBPHRecognizer*>(this) != 0)
	{
		dynamic_cast<MyLBPHRecognizer*>(this)->update(src, labels);
		return;
	}

	string error_msg = format("This custom FaceRecognizer  does not support updating, you have to use FaceRecognizer::train to update it." );
	CV_Error(CV_StsNotImplemented, error_msg);
}

void FaceRecognizer::save(const cv::String& filename) const {
	FileStorage fs(filename, FileStorage::WRITE);
	if (!fs.isOpened())
		CV_Error(CV_StsError, "File can't be opened for writing!");
	this->save(fs);
	fs.release();
}

void FaceRecognizer::load(const cv::String& filename) {
	FileStorage fs(filename, FileStorage::READ);
	if (!fs.isOpened())
		CV_Error(CV_StsError, "File can't be opened for writing!");
	this->load(fs);
	fs.release();
}

template <typename _Tp> static
inline void elbp_(InputArray _src, OutputArray _dst, int radius, int neighbors) {
	//get matrices
	Mat src = _src.getMat();
	// allocate memory for result
	_dst.create(src.rows - 2 * radius, src.cols - 2 * radius, CV_32SC1);
	Mat dst = _dst.getMat();
	// zero
	dst.setTo(0);
	for (int n = 0; n<neighbors; n++) {
		// sample points
		float x = static_cast<float>(radius * cos(2.0*CV_PI*n / static_cast<float>(neighbors)));
		float y = static_cast<float>(-radius * sin(2.0*CV_PI*n / static_cast<float>(neighbors)));
		// relative indices
		int fx = static_cast<int>(floor(x));
		int fy = static_cast<int>(floor(y));
		int cx = static_cast<int>(ceil(x));
		int cy = static_cast<int>(ceil(y));
		// fractional part
		float ty = y - fy;
		float tx = x - fx;
		// set interpolation weights
		float w1 = (1 - tx) * (1 - ty);
		float w2 = tx  * (1 - ty);
		float w3 = (1 - tx) *      ty;
		float w4 = tx  *      ty;
		// iterate through your data
		for (int i = radius; i < src.rows - radius; i++) {
			for (int j = radius; j < src.cols - radius; j++) {
				// calculate interpolated value
				float t = static_cast<float>(w1*src.at<_Tp>(i + fy, j + fx) + w2*src.at<_Tp>(i + fy, j + cx) + w3*src.at<_Tp>(i + cy, j + fx) + w4*src.at<_Tp>(i + cy, j + cx));
				// floating point precision, so check some machine-dependent epsilon
				dst.at<int>(i - radius, j - radius) += ((t > src.at<_Tp>(i, j)) || (std::abs(t - src.at<_Tp>(i, j)) < std::numeric_limits<float>::epsilon())) << n;
			}
		}
	}
}

static void elbp(InputArray src, OutputArray dst, int radius, int neighbors)
{
	int type = src.type();
	switch (type) {
	case CV_8SC1:   elbp_<char>(src, dst, radius, neighbors); break;
	case CV_8UC1:   elbp_<unsigned char>(src, dst, radius, neighbors); break;
	case CV_16SC1:  elbp_<short>(src, dst, radius, neighbors); break;
	case CV_16UC1:  elbp_<unsigned short>(src, dst, radius, neighbors); break;
	case CV_32SC1:  elbp_<int>(src, dst, radius, neighbors); break;
	case CV_32FC1:  elbp_<float>(src, dst, radius, neighbors); break;
	case CV_64FC1:  elbp_<double>(src, dst, radius, neighbors); break;
	default:
		string error_msg = format("Using Original Local Binary Patterns for feature extraction only works on single-channel images (given %d). Please pass the image data as a grayscale image!", type);
		CV_Error(CV_StsNotImplemented, error_msg);
		break;
	}
}

static Mat
histc_(const Mat& src, int minVal = 0, int maxVal = 255, bool normed = false)
{
	Mat result;
	// Establish the number of bins.
	int histSize = maxVal - minVal + 1;
	// Set the ranges.
	float range[] = { static_cast<float>(minVal), static_cast<float>(maxVal + 1) };
	const float* histRange = { range };
	// calc histogram
	calcHist(&src, 1, 0, Mat(), result, 1, &histSize, &histRange, true, false);
	// normalize
	if (normed) {
		result /= (int)src.total();
	}
	return result.reshape(1, 1);
}

static Mat histc(InputArray _src, int minVal, int maxVal, bool normed)
{
	Mat src = _src.getMat();
	switch (src.type()) {
	case CV_8SC1:
		return histc_(Mat_<float>(src), minVal, maxVal, normed);
		break;
	case CV_8UC1:
		return histc_(src, minVal, maxVal, normed);
		break;
	case CV_16SC1:
		return histc_(Mat_<float>(src), minVal, maxVal, normed);
		break;
	case CV_16UC1:
		return histc_(src, minVal, maxVal, normed);
		break;
	case CV_32SC1:
		return histc_(Mat_<float>(src), minVal, maxVal, normed);
		break;
	case CV_32FC1:
		return histc_(src, minVal, maxVal, normed);
		break;
	default:
		CV_Error(CV_StsUnmatchedFormats, "This type is not implemented yet."); break;
	}
	return Mat();
}

static Mat spatial_histogram(InputArray _src, int numPatterns,
	int grid_x, int grid_y, bool /*normed*/)
{
	Mat src = _src.getMat();
	// calculate LBP patch size
	int width = src.cols / grid_x;
	int height = src.rows / grid_y;
	// allocate memory for the spatial histogram
	Mat result = Mat::zeros(grid_x * grid_y, numPatterns, CV_32FC1);
	// return matrix with zeros if no data was given
	if (src.empty())
		return result.reshape(1, 1);
	// initial result_row
	int resultRowIdx = 0;
	// iterate through grid
	for (int i = 0; i < grid_y; i++) {
		for (int j = 0; j < grid_x; j++) {
			Mat src_cell = Mat(src, Range(i*height, (i + 1)*height), Range(j*width, (j + 1)*width));
			Mat cell_hist = histc(src_cell, 0, (numPatterns - 1), true);
			// copy to the result matrix
			Mat result_row = result.row(resultRowIdx);
			cell_hist.reshape(1, 1).convertTo(result_row, CV_32FC1);
			// increase row count in result matrix
			resultRowIdx++;
		}
	}
	// return result as reshaped feature vector
	return result.reshape(1, 1);
}

//------------------------------------------------------------------------------
// wrapper to cv::elbp (extended local binary patterns)
//------------------------------------------------------------------------------

static Mat elbp(InputArray src, int radius, int neighbors) {
	Mat dst;
	elbp(src, dst, radius, neighbors);
	return dst;
}

template<typename _Tp>
inline void readFileNodeList(const FileNode& fn, vector<_Tp>& result) {
	if (fn.type() == FileNode::SEQ) {
		for (FileNodeIterator it = fn.begin(); it != fn.end();) {
			_Tp item;
			it >> item;
			result.push_back(item);
		}
	}
}

template<typename _Tp>
inline void writeFileNodeList(FileStorage& fs, const string& name,
	const vector<_Tp>& items) {
	// typedefs
	typedef typename vector<_Tp>::const_iterator constVecIterator;
	// write the elements in item to fs
	fs << name << "[";
	for (constVecIterator it = items.begin(); it != items.end(); ++it) {
		fs << *it;
	}
	fs << "]";
}

void MyLBPHRecognizer::load(const FileStorage& fs) {
	fs["radius"] >> _radius;
	fs["neighbors"] >> _neighbors;
	fs["grid_x"] >> _grid_x;
	fs["grid_y"] >> _grid_y;
	//read matrices
	readFileNodeList(fs["histograms"], _histograms);
	fs["labels"] >> _labels;
}

void MyLBPHRecognizer::save(FileStorage& fs) const {
	//fs << "radius" << _radius;
	//fs << "neighbors" << _neighbors;
	//fs << "grid_x" << _grid_x;
	//fs << "grid_y" << _grid_y;
	//// write matrices
	//writeFileNodeList(fs, "histograms", _histograms);
	//fs << "labels" << _labels;
}

void MyLBPHRecognizer::train(InputArrayOfArrays _in_src, InputArray _in_labels) {
	//this-train(_in_src, _in_labels, false);
}

void MyLBPHRecognizer::predict(InputArray _src, int &minClass, double &minDist) const {
	if (_histograms.empty()) {
		// throw error if no data (or simply return -1?)
		string error_message = "This LBPH model is not computed yet. Did you call the train method?";
		CV_Error(CV_StsBadArg, error_message);
	}
	Mat src = _src.getMat();
	// get the spatial histogram from input image
	Mat lbp_image = elbp(src, _radius, _neighbors);
	Mat query = spatial_histogram(
		lbp_image, /* lbp_image */
		static_cast<int>(std::pow(2.0, static_cast<double>(_neighbors))), /* number of possible patterns */
		_grid_x, /* grid size x */
		_grid_y, /* grid size y */
		true /* normed histograms */);
	// find 1-nearest neighbor
	minDist = DBL_MAX;
	minClass = -1;
	for (size_t sampleIdx = 0; sampleIdx < _histograms.size(); sampleIdx++) {
		double dist = compareHist(_histograms[sampleIdx], query, CV_COMP_CHISQR);
		if ((dist < minDist) && (dist < _threshold)) {
			minDist = dist;
			minClass = _labels.at<int>((int)sampleIdx);
		}
	}
}

int MyLBPHRecognizer::predict(InputArray _src) const {
	int label;
	double dummy;
	predict(_src, label, dummy);
	return label;
}

bool mycomparator(pair<double, int> i, pair<double, int> j) { return (i.first<j.first); }
bool mycomparator2(pair<int, double> i, pair<int, double> j) { return (i.second>j.second); }

void MyLBPHRecognizer::predict(InputArray _src, bool useThreshold, int neighbors, int &minClass) const {
	double minDist;
	vector<pair<double, int> > distances;
	vector<pair<int, double> > bins;
	if (_histograms.empty()) {
		// throw error if no data (or simply return -1?)
		string error_message = "This LBPH model is not computed yet. Did you call the train method?";
		CV_Error(CV_StsBadArg, error_message);
	}
	Mat src = _src.getMat();
	// get the spatial histogram from input image
	Mat lbp_image = elbp(src, _radius, _neighbors);
	Mat query = spatial_histogram(
		lbp_image, /* lbp_image */
		static_cast<int>(std::pow(2.0, static_cast<double>(_neighbors))), /* number of possible patterns */
		_grid_x, /* grid size x */
		_grid_y, /* grid size y */
		true /* normed histograms */);
	// find 1-nearest neighbor
	minDist = DBL_MAX;
	minClass = -1;
	
	for (size_t sampleIdx = 0; sampleIdx < _histograms.size(); sampleIdx++) {
		double dist = compareHist(_histograms[sampleIdx], query, CV_COMP_CHISQR);
		/*if ((dist < minDist) && (dist < _threshold)) {
			minDist = dist;
			minClass = _labels.at<int>((int)sampleIdx);
		}*/
		if (useThreshold)
		{
			if (dist < _threshold)
				distances.push_back(make_pair(dist, _labels.at<int>((int)sampleIdx)));
		}
		else
			distances.push_back(make_pair(dist, _labels.at<int>((int)sampleIdx)));
	}
	if (distances.size() < 2)
	{
		if (distances.size() == 0)
		{
			minClass = -1;
			return;
		}
		else
		{
			minClass = distances.at(0).second;
			return;
		}
	}

	for (int i = 0; i < _classes; i++)
		bins.push_back(make_pair(i, 0.0));

	sort(distances.begin(), distances.end(), mycomparator);

	//int finalNeighbors=0;	
	//for (size_t i = 0; i < min(neighbors, (int)(distances.size() - 1)); i++)
	//{
	//	cout << (distances.at(i).first) / (distances.at(i + 1).first) << endl;
	//	if ((distances.at(i).first) / (distances.at(i + 1).first) < 0.5)
	//	{
	//		finalNeighbors = i;
	//		break;
	//	}
	//}
	////cout << finalNeighbors << endl;
	////cout << distances.size() << endl;

	//for (size_t i = 0; i <= finalNeighbors; i++)
	//	bins.at(distances.at(i).second).second++;

	int finalNeighbors = min(neighbors, (int)(distances.size()));
	double min_dist = distances.at(0).first;
	double max_dist = distances.at(finalNeighbors - 1).first;

	for (size_t i = 0; i < finalNeighbors; i++)
		bins.at(distances.at(i).second).second += 1.0 - ((distances.at(i).first - min_dist)/(max_dist - min_dist));
	
	sort(bins.begin(), bins.end(), mycomparator2);

	minClass = bins.at(0).first;
}
