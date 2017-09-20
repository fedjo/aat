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
from .forms import ComplexDetectionForm, DefaultDetectionForm
from utils.clock_utils import Clock
from utils.video_utils import create_annotated_video_path
from utils.general_utils import create_name_dict_from_file
from thesis.tasks import face_detection_recognition, object_detection


log = logging.getLogger(__name__)


def index(request):
    if request.method == 'GET':
        form = DefaultDetectionForm()
        context = {'boldmessage':  'Hello, this is the index page',
                   'form': form,
                   'media': ''}
        return render(request, 'thesis/index.html', context)


@Clock.time
def default_detection(request):
    if request.method == 'POST':
        form = DefaultDetectionForm(request.POST)
        if form.is_valid():
            log.debug(form.as_table())

            video_path = request.POST['video_dir']
            has_recognition = request.POST['recognizer']
            has_detection = request.POST['objdetection']

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
            if has_detection == 'true':
                has_detection = True
            else:
                has_detection = False

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
                                                            has_bounding_boxes=True,
                                                            has_obj_det=has_detection),
                               object_detection.s())()
                (framesdir, objects, names) = result.get()
                log.debug('lalala: {}'.format(framesdir))
            except Exception as e:
                log.debug(str(e))
                return HttpResponseBadRequest("Video cannot be opened!")

            log.debug("The annotated video path is {}".format(video_store_path))

            # TO TEST
            shutil.copy(video_store_path, settings.STATIC_ROOT)
            video_serve_path = os.path.join(settings.STATIC_ROOT,
                                            os.path.basename(video_store_path))
            os.remove(video_path)
            os.remove(video_store_path)
            context = {'form':  DefaultDetectionForm(),
                       'media': os.path.basename(video_serve_path),
                       'names': names,
                       'framesdir': os.path.basename(os.path.normpath(framesdir)),
                       'objects': objects}
            return render(request, 'thesis/index.html', context)
        else:
            log.error(form.errors.as_data())
            return HttpResponseBadRequest("Form is not valid")
    else:
        vidForm = ComplexDetectionForm()
        context = {'form': vidForm}
        return render(request, 'thesis/block.html', context)


@Clock.time
def complex_detection(request):
    if request.method == 'POST':
        form = ComplexDetectionForm(request.POST, request.FILES)
        if form.is_valid():
            log.debug("Form is valid!")
            log.debug(form.__dict__)

            video_file = request.FILES['video']
            # Handle ZIP uploaded video
            if request.POST['iszip'] == 'Yes':
                video_file = extract_video(video_file)
                if not os.path.exists(video_file):
                    return HttpResponseBadRequest(video_file)
            # Handle ZIP faces db if provided
            if 'facesdb' in request.FILES:
                facesdb = request.FILES['facesdb']
                if facesdb:
                    facesdb_path = extract_faces(facesdb)
                    if not os.path.exists(facesdb_path):
                        return HttpResponseBadRequest(facesdb_path)

            if isinstance(video_file, basestring):
                video_path = video_file
            else:
                shutil.copy(video_file.temporary_file_path(),
                            settings.CACHE_ROOT)
                video_path = os.path.join(settings.CACHE_ROOT,
                                          os.path.basename(video_file.temporary_file_path()))

            has_recognition = request.POST['recognizer']
            #has_detection = request.POST['objdetection']
            has_detection = True

            faces_path = os.path.join(settings.CACHE_ROOT, 'faces', 'lucce_thesisdb')
            haarcascades = [1]
            scale = form.cleaned_data['scale']
            neighbors = form.cleaned_data['neighbors']
            minx = form.cleaned_data['min_x_dimension']
            miny = form.cleaned_data['min_y_dimension']
            has_boundingboxes = form.cleaned_data['bounding_boxes']
            if has_recognition != 'No':
                recognizer_name = form.cleaned_data['recognizer']
                has_detection = False
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
                                                            has_bounding_boxes=has_boundingboxes,
                                                            has_obj_det=has_detection),
                               object_detection.s())()
                (framesdir, objects, names) = result.get()
                log.debug('lalala: {}'.format(framesdir))
                log.debug('Name: {}'.format(names))
            except Exception as e:
                log.debug(str(e))
                return HttpResponseBadRequest("Video cannot be opened!")

            log.debug("The annotated video path is {}".format(video_store_path))

            # TO TEST
            shutil.copy(video_store_path, settings.STATIC_ROOT)
            video_serve_path = os.path.join(settings.STATIC_ROOT,
                                            os.path.basename(video_store_path))
            os.remove(video_path)
            os.remove(video_store_path)
            context = {'boldmessage':  'Test Video',
                       'media': os.path.basename(video_serve_path),
                       'names': names,
                       'framesdir': os.path.basename(os.path.normpath(framesdir)),
                       'objects': objects}
            return render(request, 'thesis/index.html', context)
        else:
            log.debug(form.errors.as_data())
            form = ComplexDetectionForm()
    else:
        form = ComplexDetectionForm()

    return render(request, 'thesis/block.html', {'form': form})


# Obsolete
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

        facesno = app.create_name_dict_from_file()
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


# Obsolete
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


# Obsolete
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


def extract_video(video_zipfile):
            if not zipfile.is_zipfile(video_zipfile.temporary_file_path()):
                return "The is not a zip file"

            tmp_dir = tempfile.mkdtemp()
            zip_ref = zipfile.ZipFile(video_zipfile.temporary_file_path(), 'r')
            zip_ref.extractall(tmp_dir)
            zip_ref.close()

            files = os.listdir(tmp_dir)
            if len(files) == 0:
                mp4_path = "The zip file you uploaded does not \
                            contain any video in .mp4 format"
            if len(files) == 1:
                if '.mp4' in files[0]:
                    mp4_path = os.path.join(tmp_dir, files[0])
                else:
                    mp4_path = "The zip file you uploaded does not \
                               contain any video in .mp4 format"
            else:
                for f in files:
                    if '.mp4' in f:
                        mp4_path = os.path.join(tmp_dir, f)
            shutil.rmtree(tmp_dir)
            return mp4_path


def extract_faces(faces_zipfile):
            if not zipfile.is_zipfile(faces_zipfile.temporary_file_path()):
                return "The is not a zip file"

            tmp_dir = tempfile.mkdtemp()
            zip_ref = zipfile.ZipFile(faces_zipfile.temporary_file_path(), 'r')
            zip_ref.extractall(tmp_dir)
            zip_ref.close()

            files = os.listdir(tmp_dir)
            if len(files) == 0:
                    mp4_path = "The zip file you uploaded does not \
                               contain any file"
            else:
                return tmp_dir
