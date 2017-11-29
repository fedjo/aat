import os
import cv2
import csv
import json
import shutil
import zipfile
import logging
import tempfile
from random import randint
from celery import chain


from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, \
        HttpResponseRedirect, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

from .models import Configuration, Cascade, RecognizerPreTrainedData
from .forms import ComplexDetectionForm, DefaultDetectionForm
from utils.clock_utils import Clock
from utils.video_utils import configure_recognizer, create_annotated_video_path
from utils.general_utils import create_name_dict_from_file, create_csv_file
from thesis.tasks import face_detection_recognition, object_detection, \
                        transcribe


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
            has_subtitles = form.cleaned_data['subtitles']
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
                result_sbts = transcribe.delay(video_path)
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
@require_http_methods(['GET'])
def configure(request):

    content = dict()
    cascade = dict()
    recognizer = dict()
    objdetector = dict()

    if ('default' in request.path):

        try:
            c = Configuration.objects.get(pk=1)
        except Configuration.DoesNotExist as e:
            log.error(e)
            return HttpResponse(status=500)

        content['path'] = '/path/to/video.mp4'

        cascade['name'] = c.cascade_name
        cascade['scale'] = c.cascade_scale
        cascade['neighnors'] = c.cascade_neighbors
        cascade['min_face_size'] = c.cascade_min_face_size
        cascade['boxes'] = c.cascade_boxes

        recognizer['name'] = c.recognizer_name

        objdetector['name'] = c.objdetector_name

    else:

        content['path'] = '/path/to/video.mp4'

        cascade['name'] = '[1,2,3]'
        cascade['scale'] = '1.5'
        cascade['neighnors'] = '5'
        cascade['min_face_size'] = '30'
        cascade['boxes'] = 'yes'

        recognizer['name'] = '["LBPH", "FF", "EF"]'

        objdetector['name'] = '["default", "tensorflow"]'


    resp = dict()
    resp['cascade'] = cascade
    resp['recognizer'] = recognizer
    resp['objdetector'] = objdetector

    return JsonResponse(resp)

# This method has also to create train YAML files
# according to the faces uploaded for every recognizer
# Eighen, Fisher, LBPH
@csrf_exempt
@require_http_methods(['POST', 'GET'])
def model(request):
    if (request.method == 'POST' and
        request.FILES['file']):

        uploadedzip = request.FILES['file']
        fs = FileSystemStorage()
        zipname = fs.save(uploadedzip.name, uploadedzip)
        zippath = os.path.join(settings.MEDIA_ROOT, zipname)

        if not zipfile.is_zipfile(zippath):
            return HttpResponseBadRequest("The uploaded file is not a zip file")

        facedbdir = os.path.join(settings.MEDIA_ROOT,
                                 'faces', os.path.splitext(uploadedzip.name)[0])
        extractdir = os.path.join(facedbdir, 'faces')
        if os.path.exists(extractdir):
            extractdir += "_" + str(randint(0, 50))
        os.makedirs(extractdir)

        zip_ref = zipfile.ZipFile(zippath, 'r')
        zip_ref.extractall(extractdir)
        zip_ref.close()
        os.remove(zippath)

        size = (160, 120)
        if( ('sizex' and 'sizey') in request.POST):
            size[0] = request.POST['sizex']
            size[1] = request.POST['sizey']

        for r in ['LBPH', 'EF', 'FF']:
            configure_recognizer(r, uploadedzip.name, extractdir, size)

        people = []
        for facename in os.listdir(extractdir):
            people.append(facename)

        resp = dict()
        resp['people'] = people

        return JsonResponse(resp)
    else:
        yamls = RecognizerPreTrainedData.objects.all()
        return JsonResponse([y.to_dict() for y in yamls], safe=False)


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
