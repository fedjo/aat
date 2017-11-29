from django.conf.urls import url
from . import views

urlpatterns = [
        url(r'^complexdetection',
            views.complex_detection, name='complex_detection'),
        url(r'^defaultdetection',
            views.default_detection, name='default_detection'),
        url(r'^annotate', views.annotate, name='annotate'),
        url(r'^configure', views.configure, name='configure'),
        url(r'^model', views.model, name='model'),
        url(r'^$', views.index, name='index'),
]
