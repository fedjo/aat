from django.conf.urls import url, include
from . import views

urlpatterns = [
        url(r'^$', views.index, name='index'),
        url(r'^home', views.home, name='home'),
        url(r'^complexdetection',
            views.form_detection, name='form_detection'),
        url(r'^defaultdetection',
            views.form_detection, name='form_detection'),
        url(r'^annotate',
            views.annotate, name='annotate'),
        url(r'^configure/default', views.configure, name='configure_def'),
        url(r'^configure', views.configure, name='configure'),
        url(r'^model', views.model, name='model'),
        url(r'^', include('django.contrib.auth.urls', namespace='auth')),
        url(r'^', include('social_django.urls', namespace='social')),
]
