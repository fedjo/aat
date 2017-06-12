from os import listdir, walk, makedirs, rmdir
from os.path import isfile, join, exists, split
import timeit
import json
import shutil
import zipfile

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, \
        HttpResponseRedirect, HttpResponseBadRequest
from utils.video import Video, create_ui_video_name
from utils.clock import Clock
from .forms import VideoForm
from .forms import PostForm
from main import App



# Create your views here.


def index(request):
    if request.method == 'GET':
        form = PostForm()
        context = { 'boldmessage' :  'Hello, this is the index page',
                    'form' : form
                }
        return render(request, 'thesis/index.html', context)

@Clock.time
def upload_video(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            print form.as_table()
            video_dir = request.POST['video_dir']
            bool_rec = request.POST['recognizer']
            obj_dec = request.POST['objdetection']
            d = {}
            recogn_name = ''
            if bool_rec == 'true':
                recogn_name = 'LBPH'
            app = App(video_dir, recogn_name)
            if True:
                objects = app.object_detection()
            d = app.create_name_dict_from_file(recogn_name)
            h, ui_video_name =  split(create_ui_video_name(video_dir, recogn_name))
            print ui_video_name
            context = {'form' :  PostForm(), 'media': ui_video_name, 'names': d,
                        'objects': objects}
            return render(request, 'thesis/index.html', context)
        else:
            print form.errors.as_data()
            return HttpResponseBadRequest("Form is not valid")
    else:
        vidForm = VideoForm()
        context = { 'form' : vidForm }
        return render(request, 'thesis/block.html', context)

@Clock.time
def process_upload(request):
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if not form.is_valid():
            form = VideoForm()
            return render(request, 'thesis/block.html', {'form': form})


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

            shutil.rmtree('/tmp/video/')
        # #################

        if form.is_valid():
            print "OK"
            rec = ""
            if request.POST['recognizer'] != 'No':
                rec = form.recognizer
            app = App(video,
                        rec,
                        request.POST['Scale'],
                        request.POST['Neighbors'],
                        request.POST['Min_X_dimension'],
                        request.POST['Min_Y_dimension']
                            )
            objects = app.object_detect()
            h, ui_video_name = split(create_ui_video_name(video, rec))
            context = { 'boldmessage' :  "Test video", 'media': ui_video_name,
                        'objects': objects}
            return render(request, 'thesis/index.html', context)
        else:
            print form.errors.as_table()
            form = VideoForm()
    else:
        form = VideoForm()

    return render(request, 'thesis/block.html', {'form': form})

def annotate(request):
    if request.method == 'POST':
        if request.FILES['video']:
            uploadedf = request.FILES['video']

        elif request.POST['video']:
            videourl = request.POST['video']

        # process uploaded file


        resp = dict()
        meta = dict()
        tags = dict()

        resp['meta'] = meta
        resp ['tags'] = tags

        return JsonResponse(resp)
    else:
        return HttpResponseBadRequest


def configure(request):
    if request.method == 'GET':

        cascade = dict()
        recognizer = dict()
        objdetector = dict()
        resp = dict()

    elif request.method == 'POST':

        jsonconf = json.loads(request.body)
        # Parse configuration JSON
        # cascade, recognizer, objdetector = parse_jsonconf(jsonconf)

    else:
        return HttpResponseBadRequest

    resp['cascade'] = cascade
    resp['recognizer'] = recognizer
    resp['objdetector'] = odjdetector

    return JsonResponse(resp)


def model(request):
    if (request.method == 'POST' and
        request.FILES['model']):

        uploadedzip = request.FILE['model']
        # Unzip file and parse content

        people = []
        resp = dict()

        return JsonResponse(resp)
    else:
        return HttpResponseBadRequest


@Clock.time
def parse_directory(request):
    dr = "/media/yiorgos/Maxtor/thesis_video/eu_screen_SD/"
    # dr = request.POST['dir']
    videos = []
    for(dirpath, dirnames, filenames) in walk(dr):
        for f in filenames:
            #if f.endswith('.mp4') or f.endswith('.mov'):
            if f.endswith('.mp4'):
                videos.append(join(dirpath, f))
    #print videos
    for v in videos:
        for r in ['LBPH', 'FF', 'EF']:
            App(v, r)
    return HttpResponse("Videos parsed!")



