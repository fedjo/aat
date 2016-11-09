from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from utils.video import Video
from utils.clock import Clock
from .forms import VideoForm
from .forms import PostForm
from main import App 
import timeit


# Create your views here.

def index(request):
    if request.method == 'GET':        
        form = PostForm()
        context = { 'boldmessage' :  'Hello, this is the index page',
                    'form' : form    
                }
        return render(request, 'thesis/index.html', context)

def upload_video(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        video_dir = request.POST['video_dir']
        if form.is_valid():
            vidForm = VideoForm(initial={'video_dir': video_dir})
            context = { 'form' : vidForm }
            return render(request, 'thesis/form.html', context)
    else:
        vidForm = VideoForm()
        context = { 'form' : vidForm }
        return render(request, 'thesis/form.html', context)
        
@Clock.time
def process_upload(request):
    if request.method == 'POST':
        #request.upload_handlers.pop(0)
        form = VideoForm(request.POST, request.FILES)
        video = ""
        if hasattr(form, 'video'):
            video = form.video
        #if form.is_valid():
        app = App(video, 
                    request.POST['recognizer'],
                    request.POST['video_dir'] 
                    )
        context = { 'boldmessage' :  "Test video", 'media': "images/output.mp4"  }
        return render(request, 'thesis/index.html', context)
    else:
        form = VideoForm()
    return render(request, 'thesis/form.html', {'form': form})
