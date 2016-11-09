from utils.video import Video

class App:

    def __init__(self, filename, recognizer, video_dir):

            if filename is not "":
                print(filename.temporary_file_path(), ' ** ', recognizer, ' ** ',
                       video_dir)
            else:
                print(filename, ' ** ', recognizer, ' ** ',
                       video_dir)

            if not video_dir:
                video = Video(filename.temporary_file_path()) 
            else:
                video = Video(video_dir)
            if recognizer and True:
                video.setRecognizer(recognizer)
                video.detectFaces(True)
            else:
                video.detectFaces(False)

