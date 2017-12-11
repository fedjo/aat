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
from aat.tasks import face_detection_recognition, transcribe, object_detection2


log = logging.getLogger(__name__)


def index(request):
    if request.method == 'GET':
        form = DefaultDetectionForm()
        context = {'boldmessage':  'Hello, this is the index page',
                   'form': form,
                   'media': ''}
        return render(request, 'aat/index.html', context)


@csrf_exempt
@require_http_methods(['GET'])
def configure(request):
    """This method either returns the default configuration of the tool or
    returns and example configuration with possible values on every field"""

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
    resp['content'] = content
    resp['cascade'] = cascade
    resp['recognizer'] = recognizer
    resp['objdetector'] = objdetector

    return JsonResponse(resp)

@csrf_exempt
@require_http_methods(['POST', 'GET'])
def model(request):
    """This method has also to create train YAML files  according to the
    faces uploaded for every recognizer Eighen, Fisher, LBPH """

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


@csrf_exempt
@require_http_methods(['POST'])
def annotate(request):
    jsondata = json.loads(request.body)
    context = process_form(request, jsondata)
    with open(context['annotations_file'], 'r') as an:
        return HttpResponse(an.read())
    return JsonResponse(jsondata)


@Clock.time
@require_http_methods(['POST', 'GET'])
def form_detection(request):
    if request.method == 'POST':
        log.debug(request.POST)
        # POST request starts the annotation process
        if ('complex' in request.path):
            formclass =  ComplexDetectionForm
            form = formclass(request.POST, request.FILES)
        else:
            formclass = DefaultDetectionForm
            form = formclass(request.POST)

        if form.is_valid():
            log.debug(form.__dict__)
            jsondata = dict()

            if(isinstance(form, DefaultDetectionForm)):
                video_path = get_upload_path(request.FILES['video'], 'No')

                jsondata['content'] = dict()
                jsondata['content']['path'] = video_path
                #jsondata['content']['path'] = request.POST['video_dir']

                if (request.POST['detection'] == 'true'):
                    jsondata['cascade'] = dict()
                    jsondata['cascade']['name'] = [1]
                    jsondata['cascade']['scale'] = 1.3
                    jsondata['cascade']['neighbors'] = 5
                    jsondata['cascade']['minx'] = 30
                    jsondata['cascade']['miny'] = 30

                if (request.POST['recognizer'] == 'true'):
                    jsondata['recognizer'] = dict()
                    jsondata['recognizer']['name'] = 'LBPH'
                if (request.POST['objdetection'] == 'true'):
                    jsondata['objdetector'] = dict()
                    jsondata['objdetector']['name'] = 'SSD_Mobilenet'
                if (request.POST['transcription'] == 'true'):
                    jsondata['transcription'] = 'true'

                jsondata['bounding_boxes'] = 'True'

            elif(isinstance(form, ComplexDetectionForm)):
                video_path = get_upload_path(request.FILES['video'],
                                             request.POST['iszip'])

                # Handle ZIP faces db if provided
                if 'facesdb' in request.FILES:
                    facesdb = request.FILES['facesdb']
                    if facesdb:
                        facesdb_path = extract_faces(facesdb)
                        if not os.path.exists(facesdb_path):
                            return HttpResponseBadRequest(facesdb_path)


                jsondata['content'] = dict()
                jsondata['content']['path'] = video_path

                if (request.POST['detection'] == 'true'):
                    jsondata['cascade'] = dict()
                    jsondata['cascade']['name'] = [1]
                    jsondata['cascade']['scale'] = form.cleaned_data['scale']
                    jsondata['cascade']['neighbors'] = form.cleaned_data['neighbors']
                    jsondata['cascade']['minx'] = form.cleaned_data['min_x_dimension']
                    jsondata['cascade']['miny'] = form.cleaned_data['min_y_dimension']

                if (request.POST['recognizer'] != 'false'):
                    jsondata['recognizer'] = dict()
                    jsondata['recognizer']['name'] = form.cleaned_data['recognizer']
                if (request.POST['objdetection'] == 'true'):
                    jsondata['objdetector'] = dict()
                    jsondata['objdetector']['name'] = 'SSD_Mobilenet'
                if (request.POST['transcription'] == 'true'):
                    jsondata['transcription'] = 'true'

                jsondata['bounding_boxes'] = form.cleaned_data['bounding_boxes']

            log.debug('The json created is: ')
            log.debug(jsondata)
            context = process_form(request, jsondata)
            if not context:
                return HttpResponseBadRequest("Could not process video")
            return render(request, 'aat/index.html', context)
        else:
            log.debug(form.errors.as_data())
            return HttpResponseBadRequest("Please specify the fields missing in the form")
            vidform = formclass()
            return render(request, 'aat/block.html', {'form': vidform})
    else:
        # GET request forwards to CompleDetectionForm
        vidform = ComplexDetectionForm()
        return render(request, 'aat/block.html', {'form': vidform})


def process_form(request, jsondata):

    # Create video and annotations file
    log.debug('Video path is {}'.format(jsondata['content']['path']))
    video_store_path = create_annotated_video_path(jsondata)
    annot_text_file = os.path.join(settings.CACHE_ROOT,
                            os.path.basename(video_store_path).split('.')[0]+'.txt')
    try:
        names = dict()
        positions = dict()
        objects = dict()
        static_srt = ''

        if ('cascade' in jsondata.keys()):

            # Print values for face detection with Viola-Jones
            log.debug("The values provided are: scale {}, neighbors {},"
                      "min x dimension {}, min y dimension {}"
                      .format(jsondata['cascade']['scale'], jsondata['cascade']['neighbors'],
                              jsondata['cascade']['minx'], jsondata['cascade']['miny']))

            # Check whether we need recognition
            if 'recognizer' in jsondata.keys():
                # Selected facedb for recognition
                faces_path = os.path.join(settings.CACHE_ROOT, 'faces', 'lucce_thesisdb')
                log.debug('Selected recognizer is {}'.format(jsondata['recognizer']['name']))
                log.debug('The faces database has name {}'.format(faces_path))
                recognizer_name = jsondata['recognizer']['name']
            else:
                faces_path = ''
                recognizer_name = ''

            result = face_detection_recognition.delay(jsondata['content']['path'],
                                                      video_store_path,
                                                      recognizer_name,
                                                      faces_path,
                                                      jsondata['cascade']['name'],
                                                      jsondata['cascade']['scale'],
                                                      jsondata['cascade']['neighbors'],
                                                      jsondata['cascade']['minx'],
                                                      jsondata['cascade']['miny'],
                                                      has_bounding_boxes=jsondata['bounding_boxes'])
            (positions, names) = result.get(timeout=None)
            log.debug('Names found by recognition: {}'.format(names))

        if('objdetector' in jsondata.keys()):
            result2 = object_detection2.delay(jsondata['content']['path'],
                                              video_store_path)
            objects = result2.get(timeout=None)
            log.debug("Objects:")
            log.debug(objects)
        if ('transcription' in jsondata.keys()):
            result_sbts = transcribe.delay(jsondata['content']['path'])
            srt_path = result_sbts.get(timeout=None)
            shutil.copy(srt_path, settings.STATIC_ROOT)
            static_srt = os.path.join(settings.STATIC_ROOT,
                                      os.path.basename(srt_path))
            os.remove(srt_path)
            log.debug("Served SRT file is located here: {}".format(static_srt))
    except Exception as e:
        log.debug(str(e))
        return {}

    # TO TEST
    log.debug("The annotated video path is {}".format(video_store_path))
    shutil.copy(video_store_path, settings.STATIC_ROOT)
    video_serve_path = os.path.join(settings.STATIC_ROOT,
                                    os.path.basename(video_store_path))
    os.remove(video_store_path)
    # Send all information back to UI
    context = {'form':  DefaultDetectionForm(),
               'media': os.path.basename(video_serve_path),
               'annotations_file': annot_text_file,
               'names': names,
               'positions': positions,
               'objects': objects,
               'srt_file': static_srt}
    return context


def get_upload_path(upload, iszip):

    # Handle zip uploaded file
    if (iszip == 'Yes'):
        video_file = extract_video(upload)
        if not os.path.exists(video_file):
            return HttpResponseBadRequest(video_file)

    if isinstance(upload, basestring):
        video_path = upload
    else:
        # In most cases execution goes here!
        shutil.copy(upload.temporary_file_path(),
                    settings.CACHE_ROOT)
        video_path = os.path.join(settings.CACHE_ROOT,
                                  os.path.basename(upload.temporary_file_path()))

    return video_path


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
