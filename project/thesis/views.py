import os
import csv
import json
import shutil
import zipfile
import logging
import tempfile
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


log = logging.getLogger(__name__)


def index(request):
    if request.method == 'GET':
        form = PostForm()
        context = {'boldmessage':  'Hello, this is the index page',
                   'form': form,
                   'media': ''}
        return render(request, 'thesis/index.html', context)


@Clock.time
def default_detection(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            log.debug(form.as_table())

            video_path = request.POST['video_dir']
            has_recognition = request.POST['recognizer']
            has_detection = request.POST['objdetection']

            log.debug('Video path is {} and recognizer {}'
                      .format(video_path, recognizer_name))
            log.debug("The values provided are: scale {}, neighbors {},"
                      "min x dimension {}, min y dimension {}"
                      .format(1.3, 3, 30, 30))

            d = dict()
            video = Video(video_path)
            if has_recognition == 'true':
                recognizer_name = 'LBPH'
                video.setRecognizer(recognizer_name)
                video.detectFaces(scale=1.3, neighbors=3, minx=30,
                                  miny=30, useRecognition=True)
                d = create_name_dict_from_file(recognizer_name)
            else:
                recognizer_name = ''
                video.detectFaces(scale=1.3, neighbors=3, minx=30,
                                  miny=30, useRecognition=False)

            #if has_detection:
                #objects = video.perform_obj_detection()

            h, ui_video_name = os.path.split(
                    create_ui_video_name(video_path, recognizer_name))
            log.debug(ui_video_name)

            context = {'form':  PostForm(), 'media': ui_video_name, 'names': d,
                       'objects': objects}
            return render(request, 'thesis/index.html', context)
        else:
            log.error(form.errors.as_data())
            return HttpResponseBadRequest("Form is not valid")
    else:
        vidForm = VideoForm()
        context = {'form': vidForm}
        return render(request, 'thesis/block.html', context)


@Clock.time
def complex_detection(request):
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if not form.is_valid():
            form = VideoForm()
            return render(request, 'thesis/block.html', {'form': form})

        video_file = request.FILES['video']
        # Handle ZIP files
        if request.POST['iszip'] == 'Yes':
            if not zipfile.is_zipfile(video_file.temporary_file_path()):
                return HttpResponseBadRequest("The is not a zip file")

            tmp_dir = tempfile.mkdtemp()
            zip_ref = zipfile.ZipFile(video_file.temporary_file_path(), 'r')
            zip_ref.extractall(tmp_dir)
            zip_ref.close()

            files = os.listdir(tmp_dir)
            if len(files) == 1:
                if '.mp4' in files[0]:
                    video_file = os.path.join(tmp_dir, files[0])
                else:
                    return HttpResponseBadRequest("The zip file you uploaded does not \
                            contain any video in .mp4 format")
            else:
                video_file = ""
                for f in files:
                    if '.mp4' in f:
                        video_file = os.path.join(tmp_dir, f)
                if video_file == "":
                    return HttpResponseBadRequest("The zip file you uploaded does not \
                            contain any video in .mp4 format")

            shutil.rmtree(tmp_dir)
        # #################

        if form.is_valid():
            log.debug("Form is valid!")

            d = dict()
            if isinstance(video_file, basestring):
                video_path = video_file
            else:
                video_path = video_file.temporary_file_path()
            video = Video(video_path)
            if request.POST['recognizer'] != 'No':
                log.debug(form.__dict__)
                recognizer_name = form.cleaned_data['recognizer']
                video.setRecognizer(recognizer_name)
                video.detectFaces(scale=request.POST['Scale'],
                                  neighbors=request.POST['Neighbors'],
                                  minx=request.POST['Min_X_dimension'],
                                  miny=request.POST['Min_Y_dimension'],
                                  useRecognition=True)
                d = create_name_dict_from_file(recognizer_name)
            else:
                recognizer_name = ''
                video.detectFaces(scale=request.POST['Scale'],
                                  neighbors=request.POST['Neighbors'],
                                  minx=request.POST['Min_X_dimension'],
                                  miny=request.POST['Min_Y_dimension'],
                                  useRecognition=False)

            #objects = video.perform_obj_detection()

            h, ui_video_name = os.path.split(
                    create_ui_video_name(video_path, recognizer_name))
            context = {'boldmessage':  "Test video", 'media': ui_video_name,
                       'objects': objects}
            return render(request, 'thesis/index.html', context)
        else:
            log.debug(form.errors.as_table())
            form = VideoForm()
    else:
        form = VideoForm()

    return render(request, 'thesis/block.html', {'form': form})


@csrf_exempt
def annotate(request):
    if request.method == 'POST':
        if request.FILES['video']:
            video_file = request.FILES['video_file']
            video_path = video_file.temporary_file_path()

        elif request.POST['video']:
            # Actually path here is a url which
            # needs to be resolved`
            video_url = request.POST['video']
            #TODO
            # Resolve video_url and assign it
            # video_path
            video_path = ''

        video = Video(video_path)
        recognizer_name = request.POST['recognizer']
        if not recognizer_name:
            recognizer_name = 'LBPH'
        video.setRecognizer(recognizer_name)
        video.detectFaces(scale=1.3,
                          neighbors=3,
                          minx=30,
                          miny=30,
                          useRecognition=True)
        #video.detectFaces(scale=request.POST['Scale'],
                          #neighbors=request.POST['Neighbors'],
                          #minx=request.POST['Min_X_dimension'],
                          #miny=request.POST['Min_Y_dimension'],
                          #useRecognition=True)

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
        resp['tags'] = tags

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
        zippath = os.path.join(settings.MEDIA_ROOT, 'model.zip')
        with open(zippath, 'wb+') as destination:
            for chunk in uploadedzip.chunks():
                destination.write(chunk)

        if not zipfile.is_zipfile(zippath):
            return HttpResponseBadRequest("The is not a zip file")

        extractdir = os.path.join(settings.MEDIA_ROOT, 'faces', os.path.splitext(uploadedname))
        if os.path.exists(extractdir):
            extractdir += "_" + str(randint(0, 9))
        os.makedirs(extractdir)

        zip_ref = zipfile.ZipFile(zippath, 'r')
        zip_ref.extractall(extractdir)
        zip_ref.close()
        os.remove(zippath)

        # TODO
        # Create faces.csv and face_labels.txt file
        create_csv(extractdir, ';')

        people = []
        for facename in os.listdir(extractdir):
            people.append(facename)

        resp = dict()
        resp['people'] = people

        return JsonResponse(resp)
    else:
        return HttpResponseBadRequest


def create_csv(path, separator):
    label = 0
    topdir, folder = os.path.split(path)
    csvpath = os.path.join(topdir, folder+'.csv')
    with open(csvpath, 'wb') as csvfile:
        face_writer = csv.writer(csvfile, delimeter=separator)
        for dirname, dirnames, filenames in os.walk(path):
            for subdirname in dirnames:
                subject_path = os.path.join(dirname, subdirname)
                for filename in os.listdir(subject_path):
                    abs_path = "%s/%s" % (subject_path, filename)
                    face_writer.writerow([abs_path, label])
                label = label + 1


@Clock.time
def parse_directory(request):
    dr = "/media/yiorgos/Maxtor/thesis_video/eu_screen_SD/"
    # dr = request.POST['dir']
    videos = []
    for(dirpath, dirnames, filenames) in os.walk(dr):
        for f in filenames:
            # if f.endswith('.mp4') or f.endswith('.mov'):
            if f.endswith('.mp4'):
                videos.append(os.path.join(dirpath, f))
    # print videos
    for v in videos:
        for r in ['LBPH', 'FF', 'EF']:
            App(v, r)
    return HttpResponse("Videos parsed!")


def create_name_dict_from_file(rec):
    if not rec:
        return
    d = {}
    with open(os.path.join('/tmp', 'faces_in_current_video.txt'), 'r') as f:
        lines = f.readlines()
        for key in lines:
            if key in d:
                d[key] += 1
            else:
                d[key] = 1
    os.remove(os.path.join('/tmp', 'faces_in_current_video.txt'))
    return d
