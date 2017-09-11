from os import listdir, walk, makedirs, rmdir
from os.path import isfile, join, exists, split
import os
import timeit
import json
import shutil
import zipfile
from random import randint

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, \
        HttpResponseRedirect, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import Configuration
from utils.video import Video, create_ui_video_name
from utils.clock import Clock
from .forms import VideoForm
from .forms import PostForm
from main import App


def index(request):
    if request.method == 'GET':
        form = PostForm()
        context = { 'boldmessage' :  'Hello, this is the index page',
                    'form' : form,
                    'media':''
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
            if bool_rec == 'true':
                recogn_name = 'LBPH'
            else:
                recogn_name = ''
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
            if request.POST['recognizer'] != 'No':
                rec = form.recognizer
            else:
                rec = ''
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


@csrf_exempt
def example(request):
    try:
        data = json.loads(request.body)
        print data
    except:
        return HttpResponseBadRequest()
    return JsonResponse({'status': 'ok'})


def annotate(request):
    if request.method == 'POST':
        if request.FILES['video']:
            uploadedf = request.FILES['video']
            app = App(uploadedf, recogn_name)

        elif request.POST['video']:
            videourl = request.POST['video']
            app = App(videourl, recogn_name)

        # process uploaded file
        if True:
            objects_dict = app.object_detection()
        facesno = app.create_name_dict_from_file(recogn_name)

        faces = facesno.dict.keys()
        confidenece = facesno.values()
        objects = objects_dict.keys()
        probabilities = objects_dict.values()

        resp = dict()
        meta = dict()
        tags = dict()

        tags['faces'] = faces
        tags['confidence'] = confidence
        tags['objects'] = objects
        tags['probabilities'] = probabilities
        resp['meta'] = meta
        resp ['tags'] = tags

        return JsonResponse(resp)
    else:
        return HttpResponseBadRequest


@csrf_exempt
def configure(request):
    if request.method == 'GET':

        cascade = dict()
        recognizer = dict()
        objdetector = dict()

        c = Configuration.objects.get(pk=1)
        cascade['name'] = c.cascade_name
        cascade['scale'] = c.cascade_scale
        cascade['neighnors'] = c.cascade_neighbors
        cascade['min_face_size'] = c.cascade_min_face_size
        cascade['boxes'] = c.cascade_boxes

        recognizer['name'] = c.recognizer_name

        objdetector['name'] = c.objdetector_name

    elif request.method == 'POST':

        jsonconf = json.loads(request.body)
        cascade = jsonconf['cascade']
        recognizer = jsonconf['recognizer']
        objdetector = jsonconf['objdetector']

        c = Configuration()
        c.cascade_name = cascade['name']
        c.cascade_scale = cascade['scale']
        c.cascade_neighbors = cascade['neighbors']
        c.cascade_min_face_size = cascade['min_face_size']
        c.cascade_boxes = cascade['boxes']

        c.recognizer_name = recognizer
        c.objdetector_name = objdetector
        c.manual_tags = jsonconf['manual_tags']

        c.save()

        # Parse configuration JSON
        # cascade, recognizer, objdetector = parse_jsonconf(jsonconf)

    else:
        return HttpResponseBadRequest

    resp = dict()
    resp['cascade'] = cascade
    resp['recognizer'] = recognizer
    resp['objdetector'] = objdetector

    return JsonResponse(resp)


@csrf_exempt
def model(request):
    if (request.method == 'POST' and
        request.FILES['model']):

        uploadedzip = request.FILES['model']
        uploadedname = request.FILES['model'].name
        # Unzip file and parse content
        zippath = join(settings.MEDIA_ROOT, 'model.zip')
        with open(zippath, 'wb+') as destination:
            for chunk in uploadedzip.chunks():
                destination.write(chunk)

        if not zipfile.is_zipfile(zippath):
            return HttpResponseBadRequest("The is not a zip file")

        extractdir = join(settings.MEDIA_ROOT, 'faces', os.path.splitext(uploadedname))
        if exists(extractdir):
            extractdir += "_" + str(randint(0,9))
        makedirs(extractdir)

        zip_ref = zipfile.ZipFile(zippath, 'r')
        zip_ref.extractall(extractdir)
        zip_ref.close()
        os.remove(zippath)

        # TODO
        # Create faces.csv and face_labels.txt file
        create_csv(extractdir, ';')


        people = []
        for facename in listdir(extractdir):
            people.append(facename)

        resp = dict()
        resp['people'] = people

        return JsonResponse(resp)
    else:
        return HttpResponseBadRequest


def create_csv(path, separator):
    label = 0
    topdir, folder = split(path)
    csvpath = join(topdir, folder+'.csv')
    with open(csvpath, 'wb') as csvfile:
        face_writer = csv.writer(csvfile, delimeter=separator)
        for dirname, dirnames, filenames in os.walk(path):
            for subdirname in dirnames:
                subject_path = join(dirname, subdirname)
                for filename in listdir(subject_path):
                    abs_path = "%s/%s" % (subject_path, filename)
                    face_writer.writerow([abs_path, label])
                label = label + 1


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



