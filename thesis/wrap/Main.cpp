#include "MyLBPHRecognizer.h"

#include <iostream>
#include <fstream>
#include <vector>
#include <string>

using namespace cv;
using namespace std;

string detectorProf = "static/haarcascade_profileface.xml";	//0
//string detector = "static/haarcascade_frontalface_alt2.xml";	//0
string detector = "static/haarcascade_frontalface_default.xml";	//0
int input = 0;											//1
double scaleFactor = 1.1;								//2
int minNeighbors = 3;//2								//2
int minNeighborsProf = 3;//2
Size minSize = Size(0, 0);								//4
Size maxSize = Size(0, 0);								//5

vector<bool> found;
vector<double> confs;
vector<string> labels;
vector<string> jsons;
string lastAnot;

string finalJsonString;

string to_string(int a)
{
    stringstream b;
    b << a;
    return b.str();
}

string makeJsonString(string instance, double confidence, int x_min, int y_min, int width, int height, bool last)
{
	if (last)
		return "{\"instance\":\"" + instance + "\",\"localization\":{\"x_min\":" + to_string(x_min) + ",\"y_min\":" + to_string(y_min) + ",\"width\":" + to_string(width) + ",\"height\":" + to_string(height) + "}}";
	else
		return "{\"instance\":\"" + instance + "\",\"localization\":{\"x_min\":" + to_string(x_min) + ",\"y_min\":" + to_string(y_min) + ",\"width\":" + to_string(width) + ",\"height\":" + to_string(height) + "}},";
}

double rectOverlap(Rect A, Rect B)
{
	int Xmin = max(A.x, B.x);
	int Ymin = max(A.y, B.y);
	int Xmax = min(A.x + A.width, B.x + B.width);
	int Ymax = min(A.y + A.height, B.y + B.height);

	double intersection = (Ymax - Ymin)*(Xmax - Xmin);
	double completeArea = A.area() + B.area() - intersection;

	return intersection / completeArea;
}

int init()
{
	ifstream inFile("face_labels2.txt");
	if (!inFile) {
		cerr << "Label file not found!" << endl;
		return -1;
	}
	string line;
	while (getline(inFile, line))
	{
		if (line.empty()) continue;
		string line2 = line.substr(0, line.size()-1);
		labels.push_back(line2);
	}
	found.resize(labels.size());
	confs.resize(labels.size());
	jsons.resize(labels.size());
	for (int i = 0; i < labels.size(); i++)
	{
		found[i] = false;
		confs[i] = 500.0;
		jsons[i] = "";
	}
	return 0;
}

int main(int argc, const char *argv[])
{
	if (init()<0) return -1;

	MyLBPHRecognizer* model = new MyLBPHRecognizer(labels.size(), 1, 8, 8, 8, 50.0);

	string s = "mecanex_LBPHfaces_model_5.yml";
	FileStorage fs(s, cv::FileStorage::READ);
	model->load(fs);

	CascadeClassifier faceDetect;
	faceDetect.load(detector);

	CascadeClassifier faceDetectProf;
	faceDetectProf.load(detectorProf);

	vector< Rect_<int> > detected_faces;
	vector< Rect_<int> > detected_profiles;

	Mat src = imread(argv[1], CV_LOAD_IMAGE_COLOR);
	/*if (argc != 2 || !src.data)
	{
		cout << "{}";
		return -1;
	}*/

	Mat img2;
	Mat img;

	cvtColor(src, img, CV_BGR2GRAY);

	detected_faces.clear();
	detected_profiles.clear();

	faceDetect.detectMultiScale(img, detected_faces, scaleFactor, minNeighbors, 0, minSize, maxSize);
	faceDetectProf.detectMultiScale(img, detected_profiles, scaleFactor, minNeighborsProf, 0, minSize, maxSize);

	vector< Rect_<int> > finalVec;
	finalVec.clear();
	for (int i = 0; i < detected_profiles.size(); i++)
	{
		bool keep = true;
		Rect A = detected_profiles[i];
		for (int j = 0; j < detected_faces.size(); j++)
		{
			Rect B = detected_faces[j];
			if (rectOverlap(A, B) > 0.25)
			{
				keep = false;
				break;
			}
		}

		if (keep)
			finalVec.push_back(A);
	}

	vector< Rect_<int> > faceVec;
	faceVec.reserve(detected_faces.size() + finalVec.size()); // preallocate memory
	faceVec.insert(faceVec.end(), detected_faces.begin(), detected_faces.end());
	faceVec.insert(faceVec.end(), finalVec.begin(), finalVec.end());
	namedWindow("Demo", WINDOW_AUTOSIZE);
	if (faceVec.size() == 0)
	{
		cout << "{}";
	}
	else
	{
		cout << "[";
		if (faceVec.size() > 1)
		{
			for (int i = 0; i < faceVec.size() - 1; i++)
			{
				//Rect det_i = detected_faces[i];
				Rect det_i = faceVec[i];
				// Crop the face from the image
				Mat face = img(det_i);

				Mat face_resized;
				resize(face, face_resized, Size(50, 50), 0.0, 0.0, INTER_CUBIC);

				// Perform the prediction
				int prediction = -3; double confidence = 0.0;
				//model->predict(face_resized, prediction, confidence);
				model->predict(face_resized, true, 10, prediction);

				if (prediction == -1)
				{
					cout << makeJsonString("-", confidence, det_i.x, det_i.y, det_i.width, det_i.height, false);
					rectangle(img, Point(det_i.x, det_i.y), Point(det_i.x + det_i.width, det_i.y + det_i.height), CV_RGB(255, 0, 0), 2);
				}

				else
				{
					found[prediction] = true;
					if (confidence < confs[prediction])
					{
						confs[prediction] = confidence;
						jsons[prediction] = makeJsonString(labels[prediction], confidence, det_i.x, det_i.y, det_i.width, det_i.height, false);
						putText(img, labels[prediction], Point(det_i.x + 5, det_i.y + 15), FONT_HERSHEY_PLAIN, 1, CV_RGB(255, 0, 0), 1.0);
						rectangle(img, Point(det_i.x, det_i.y), Point(det_i.x + det_i.width, det_i.y + det_i.height), CV_RGB(255, 0, 0), 2);
					}
				}
			}
		}
		Rect det_i = faceVec[faceVec.size() - 1];
		// Crop the face from the image
		Mat face = img(det_i);
		Mat face_resized;
		resize(face, face_resized, Size(50, 50), 0.0, 0.0, INTER_CUBIC);

		// Perform the prediction
		int prediction; double confidence;
		model->predict(face_resized, true, 10, prediction);

		if (prediction == -1)
		{
			lastAnot = makeJsonString("-", confidence, det_i.x, det_i.y, det_i.width, det_i.height, true);
			rectangle(img, Point(det_i.x, det_i.y), Point(det_i.x + det_i.width, det_i.y + det_i.height), CV_RGB(255, 0, 0), 2);
		}

		else
		{
			found[prediction] = false;
			if (confidence < confs[prediction])
			{
				lastAnot = makeJsonString(labels[prediction], confidence, det_i.x, det_i.y, det_i.width, det_i.height, true);
				putText(img, labels[prediction], Point(det_i.x + 5, det_i.y + 15), FONT_HERSHEY_PLAIN, 1, CV_RGB(255, 0, 0), 1.0);
				rectangle(img, Point(det_i.x, det_i.y), Point(det_i.x + det_i.width, det_i.y + det_i.height), CV_RGB(255, 0, 0), 2);
			}
		}
		for (int i = 0; i < labels.size(); i++)
		{
			if (found[i])
				cout << jsons[i];
		}
		cout << lastAnot;
		cout << "]";
	}
	imshow("Demo", img);
	if (waitKey(0) == 27)
	{
		destroyWindow("Demo");
	}
	return 0;
}
