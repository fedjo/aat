from __future__ import unicode_literals

from django.db import models


class Configuration(models.Model):
    current = models.BooleanField(default=False)
    cascade_name = models.CharField(max_length=50)
    cascade_scale = models.CharField(max_length=50)
    cascade_neighbors = models.CharField(max_length=50)
    cascade_min_face_size = models.CharField(max_length=50)
    cascade_boxes = models.CharField(max_length=50)

    recognizer_name = models.CharField(max_length=50)

    objdetector_name = models.CharField(max_length=50)

    manual_tags = models.CharField(max_length=50)


class Cascade(models.Model):
    name = models.CharField(max_length=100)
    xml_file = models.FileField(upload_to='haar_cascades/')


class RecognizerPreTrainedData(models.Model):
    name = models.CharField(max_length=50)
    recognizer = models.CharField(max_length=50)
    yml_file = models.FileField(upload_to='recognizer_train_data/')
    faces = models.CharField(max_length=500, blank=True)
    csv_path = models.CharField(max_length=150, blank=True)

    def to_dict(self):
        return {
            'name': self.name,
            'recognizer': self.recognizer,
            'faces': self.faces
        }
