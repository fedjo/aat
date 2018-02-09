"""opencvFaceRec URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.http import HttpResponse
from django.conf.urls import url, include
from django.contrib import admin

from revproxy.views import ProxyView


class AdminProxyView(ProxyView):
    def dispatch(self, request, path):
        # user = request.user
        # if user.is_authenticated and user.is_active and user.is_superuser:
            # return super(AdminProxyView, self).dispatch(request, path)
        #return HttpResponse("Not authorized as admin.", status=401)
        return super(AdminProxyView, self).dispatch(request, path)


class RabbitmqAdminProxyView(AdminProxyView):
    def get_quoted_path(self, path):
        path = super(RabbitmqAdminProxyView, self).get_quoted_path(path)
        return path.replace('///', '/%2f/')


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('aat.urls')),

    # Proxy to several admin applications, only for superusers.
    url(r'^manage/rabbitmq/(?P<path>.*)$',
        RabbitmqAdminProxyView.as_view(upstream='http://rabbitmq:15672/')),
    url(r'^manage/flower/(?P<path>.*)$',
        AdminProxyView.as_view(upstream='http://flower:5555/')),

]
