from utils.video import Video

class App:

    def __init__(self, filename, recognizer, video_dir):

            self.video = Video(filename.temporary_file_path()) 
            self.video_directory = video_dir
            self.video.read_csv_file("", recognizer)
            self.video.recognDict[recognizer]()
            print(filename.temporary_file_path(), ' ** ', recognizer, ' ** ',
                    video_dir)
            self.video.detectFaces(True)

    def printVideoName(self):
            return self.video.printName()

