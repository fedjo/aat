from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseBadRequest
from utils.video import Video
from utils.clock import Clock

from os import listdir, walk, makedirs, rmdir
from os.path import isfile, join, exists
import shutil
import zipfile

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
        bool_rec = request.POST['recognizer']
        if form.is_valid():
            if bool_rec == 'true':
                App("", 'LBPH', video_dir)
            else:
                App("", "", video_dir)
            context = { 'form' :  PostForm(), 'media': "images/output.mp4"  }
            return render(request, 'thesis/index.html', context)
        else:
            return HttpResponseBadRequest("Form is not valid")
    else:
        vidForm = VideoForm()
        context = { 'form' : vidForm }
        return render(request, 'thesis/form.html', context)
        
@Clock.time
def process_upload(request):
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        video = request.FILES['video']

        # Handle ZIP files
        if request.POST['iszip'] == 'Yes':
            if not zipfile.is_zipfile(video.temporary_file_path()):
                return HttpResponseBadRequest("The is not a zip file")

            tmp_dir = '/tmp/video/'
            if not exists(tmp_dir):
                makedirs(tmp_dir)

            zip_ref = zipfile.ZipFile(video.temporary_file_path(), 'r')
            zip_ref.extractall(tmp_dir)
            zip_ref.close()
    
            files = listdir(tmp_dir)
            if len(files) == 1:
                if '.mp4' in files[0]:
                    video = join(tmp_dir, files[0])
                else:
                    return HttpResponseBadRequest("The zip file you uploaded does not \
                            contain any video in .mp4 format")
            else:
                video = ""
                for f in files:
                    if '.mp4' in f:
                        video = join(tmp_dir, f)
                if video == "":
                    return HttpResponseBadRequest("The zip file you uploaded does not \
                            contain any video in .mp4 format")
        # #################

        if form.is_valid():
            print "OK"
            rec = ""
            if request.POST['recognizer'] != 'No':
                rec = form.recognizer
            app = App(video, 
                        rec,
                        "",
                        request.POST['Scale'],
                        request.POST['Neighbors'],
                        request.POST['Min_X_dimension'],
                        request.POST['Min_Y_dimension']
                            )
            shutil.rmtree('/tmp/video/')
            context = { 'boldmessage' :  "Test video", 'media': "images/output.mp4"  }
            return render(request, 'thesis/index.html', context)
        else:
            print "OK"
            print form.errors
            form = VideoForm()
    else:
        form = VideoForm()

    return render(request, 'thesis/form.html', {'form': form})

@Clock.time
def parse_directory(request):
    dr = "/home/yiorgos/"
    # dr = request.POST['dir']
    videos = []
    for(dirpath, dirnames, filenames) in walk(dr):
        for f in filenames:
            if f.endswith('.mp4') or f.endswith('.mov'):
                videos.append(join(dirpath, f))
    #print videos
    for v in videos:
        for r in ['LBPH', 'FF', 'EF']:
            App("", r, v)
    return HttpResponse("Videos parsed!")



