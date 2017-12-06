from django.conf.urls import url
from . import views

urlpatterns = [
        url(r'^complexdetection',
            views.form_detection, name='form_detection'),
        url(r'^defaultdetection',
            views.form_detection, name='form_detection'),
        url(r'^annotate',
            views.annotate, name='annotate'),
        url(r'^configure/default', views.configure, name='configure_def'),
        url(r'^configure', views.configure, name='configure'),
        url(r'^model', views.model, name='model'),
        url(r'^$', views.index, name='index'),
]
