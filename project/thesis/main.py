from os import remove
from os.path import join, split

from django.conf import settings

from utils.video import Video
from thesis.tasks import add

class App:

    def __init__(self, filename, recognizer, scale=1.3, neighbors=3,
            Min_X_dimension=30, Min_Y_dimension=30):

            print(filename, ' ** ', recognizer, ' ** ')
            print("The values provided are: {}, {}, {}, {}".format(scale, neighbors,
                Min_X_dimension, Min_Y_dimension))

            self.video = Video(filename)
            if recognizer != "":
                self.video.setRecognizer(recognizer)
                self.video.detectFaces(scale, neighbors, Min_X_dimension, \
                        Min_Y_dimension, True)
            else:
                self.video.detectFaces(scale, neighbors, Min_X_dimension, \
                        Min_Y_dimension, False)

            sum = add.delay(99, 99).get()
            print("The task returned: {}".format(sum))


    def object_detection(self):
        return self.video.perform_obj_detection()

    def create_name_dict_from_file(self, rec):
        if not rec:
            return
        d = {}
        with open(join(settings.STATIC_ROOT, 'faces_in_current_video.txt'), 'r') as f:
            lines = f.readlines()
            for key in lines:
                if key in d:
                    d[key] += 1
                else:
                    d[key] = 1
        remove(join(settings.STATIC_ROOT, 'faces_in_current_video.txt'))
        return d

