from django.conf.urls import url
from . import views

urlpatterns = [
        url(r'^upload', views.upload_video, name='upload_video'),
        url(r'^$', views.index, name='index'),
]
