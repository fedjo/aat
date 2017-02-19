from utils.video import Video
from os import remove
from os.path import join, split

from django.conf import settings

class App:

    def __init__(self, filename, recognizer, scale=1.3, neighbors=3,
            Min_X_dimension=50, Min_Y_dimension=50):

            print(filename, ' ** ', recognizer, ' ** ')

            video = Video(filename) 
            if recognizer != "":
                video.setRecognizer(recognizer)
                video.detectFaces(True)
            else:
                video.detectFaces(False)

            video.perform_obj_detection()

    def create_name_dict_from_file(self, rec):
        if not rec:
            return
        d = {}
        with open(join(settings.STATIC_PATH, 'faces_in_current_video.txt'), 'r') as f:
            lines = f.readlines()
            for key in lines: 
                if key in d:
                    d[key] += 1
                else:
                    d[key] = 1
        remove(join(settings.STATIC_PATH, 'faces_in_current_video.txt'))
        return d
        
