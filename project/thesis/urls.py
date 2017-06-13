from django.conf.urls import url
from . import views

urlpatterns = [
        url(r'^process', views.process_upload, name='process_upload'),
        url(r'^upload', views.upload_video, name='upload_video'),
        url(r'^annotate', views.annotate, name='annotate'),
        url(r'^configure', views.configure, name='configure'),
        url(r'^model', views.model, name='model'),
        url(r'^parse', views.parse_directory, name='parse_directory'),
        url(r'^example', views.example, name='example'),
        url(r'^$', views.index, name='index'),
]
