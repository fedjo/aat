from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from utils.video import Video
from .forms import VideoForm


# Create your views here.

def index(request):
    context = { 'boldmessage' :  'Hello, this is the index page' }
    return render(request, 'thesis/index.html', context)

def upload_video(request):
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = Video(request.FILES['video'])
            video.detectFaces()
            context = { 'boldmessage' :  video.printName() }
            return render(request, 'thesis/index.html', context)
    else:
        form = VideoForm()
    return render(request, 'thesis/form.html', {'form': form})

