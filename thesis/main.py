from utils.video import Video

class App:

    def __init__(self, filename, recognizer, video_dir, scale=1.3, neighbors=3,
            Min_X_dimension=50, Min_Y_dimension=50):

            print(filename, ' ** ', recognizer, ' ** ',
                       video_dir)

            if  video_dir == "":
                video = Video(filename) 
            else:
                video = Video(video_dir)
            if recognizer != "":
                video.setRecognizer(recognizer)
                video.detectFaces(True)
            else:
                video.detectFaces(False)

