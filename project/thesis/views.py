import os
import csv
import json
import shutil
import zipfile
import logging
import tempfile
from random import randint
from celery import chain


from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, \
        HttpResponseRedirect, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import Configuration, Cascade
from utils.clock_utils import Clock
from utils.video_utils import create_annotated_video_path
from utils.general_utils import create_name_dict_from_file
from .forms import VideoForm
from .forms import PostForm
from thesis.tasks import face_detection_recognition, object_detection


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
            #has_detection = request.POST['objdetection']

            faces_path = os.path.join(settings.CACHE_ROOT, 'faces/')
            haarcascades = [1]
            scale = 1.3
            neighbors = 5
            minx = 30
            miny = 30
            if has_recognition == 'true':
                recognizer_name = 'LBPH'
            else:
                recognizer_name = ''

            log.debug('Video path is {} and recognizer {}'
                      .format(video_path, recognizer_name))
            log.debug("The values provided are: scale {}, neighbors {},"
                      "min x dimension {}, min y dimension {}"
                      .format(1.3, 3, 30, 30))

            video_store_path = create_annotated_video_path(video_path, recognizer_name)
            try:
                result = chain(face_detection_recognition.s(video_path,
                                                            video_store_path,
                                                            recognizer_name,
                                                            faces_path,
                                                            haarcascades,
                                                            scale, neighbors,
                                                            minx, miny,
                                                            has_obj_det=True),
                               object_detection.s())()
                (framesdir, objects) = result.get()
                log.debug('lalala: {}'.format(framesdir))
                names = dict()
                names = create_name_dict_from_file()
            except Exception as e:
                log.debug(str(e))
                return HttpResponseBadRequest("Video cannot be opened!")

            log.debug("The annotated video path is {}".format(video_store_path))

            video_serve_path = os.path.join(settings.STATIC_ROOT, 'video.mp4')
            shutil.copyfile(video_store_path, video_serve_path)
            context = {'form':  PostForm(),
                       'media': os.path.basename(video_serve_path),
                       'names': names,
                       'framesdir': os.path.basename(os.path.normpath(framesdir)),
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
            log.debug(form.__dict__)

            if isinstance(video_file, basestring):
                video_path = video_file
            else:
                shutil.copy(video_file.temporary_file_path(),
                            settings.CACHE_ROOT) 
                video_path = os.path.join(settings.CACHE_ROOT,
                                          os.path.basename(video_file.temporary_file_path()))

            has_recognition = request.POST['recognizer']
            #has_detection = request.POST['objdetection']

            faces_path = os.path.join(settings.CACHE_ROOT, 'faces/')
            haarcascades = [1]
            scale = form.cleaned_data['Scale']
            neighbors = form.cleaned_data['Neighbors']
            minx = form.cleaned_data['Min_X_dimension']
            miny = form.cleaned_data['Min_Y_dimension']
            if has_recognition != 'No':
                recognizer_name = form.cleaned_data['recognizer']
            else:
                recognizer_name = ''

            log.debug('Video path is {} and recognizer {}'
                      .format(video_path, recognizer_name))
            log.debug("The values provided are: scale {}, neighbors {},"
                      "min x dimension {}, min y dimension {}"
                      .format(scale, neighbors, minx, miny))

            video_store_path = create_annotated_video_path(video_path, recognizer_name)
            try:
                result = chain(face_detection_recognition.s(video_path,
                                                            video_store_path,
                                                            recognizer_name,
                                                            faces_path,
                                                            haarcascades,
                                                            scale, neighbors,
                                                            minx, miny,
                                                            has_obj_det=True),
                               object_detection.s())()
                (framesdir, objects) = result.get()
                log.debug('lalala: {}'.format(framesdir))
                names = dict()
                names = create_name_dict_from_file()
            except Exception as e:
                log.debug(str(e))
                return HttpResponseBadRequest("Video cannot be opened!")

            log.debug("The annotated video path is {}".format(video_store_path))

            video_serve_path = os.path.join(settings.STATIC_ROOT, 'video.mp4')
            shutil.copyfile(video_store_path, video_serve_path)
            context = {'boldmessage':  'Test Video',
                       'media': os.path.basename(video_serve_path),
                       'names': names,
                       'framesdir': os.path.basename(os.path.normpath(framesdir)),
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
