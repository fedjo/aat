from __future__ import unicode_literals

from django.db import models


class Configuration(models.Model):

    cascade_name = models.CharField(max_length=50)
    cascade_scale = models.CharField(max_length=50)
    cascade_neighbors = models.CharField(max_length=50)
    cascade_min_face_size = models.CharField(max_length=50)
    cascade_boxes = models.CharField(max_length=50)

    recognizer_name = models.CharField(max_length=50)

    objdetector_name = models.CharField(max_length=50)

    manual_tags = models.CharField(max_length=50)
