import os
import cv2
import csv
import json
from jsonschema import validate
import shutil
import zipfile
import logging
import tempfile
from random import randint
from celery import chord


from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from django.utils.http import urlencode
from django.http import HttpResponse, JsonResponse, \
        HttpResponseRedirect, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout

from .models import Configuration, Cascade, RecognizerPreTrainedData
from .forms import ComplexDetectionForm, DefaultDetectionForm
from utils.clock_utils import Clock
from utils.utils import exec_cmd
from utils.recognizer_utils import train
from aat.tasks import face_detection_recognition, transcribe, \
        object_detection2, senddata, returnvalues


log = logging.getLogger(__name__)


def index(request):
    return render(request, 'aat/index.html')


@login_required
def about(request):
    return render(request, 'aat/about.html')


def logout(request):

    client_id = os.environ.get('AUTH0_CLIENT_ID')
    auth_domain = os.environ.get('AUTH0_DOMAIN')

    auth_logout(request)

    params = {'returnTo': 'http://producer-toolkit.eu/#/login', 'client_id': client_id}

    return redirect('https://' + auth_domain + '/v2/logout?' + urlencode(params))


@login_required
def home(request):
    if request.method == 'GET':
        form = DefaultDetectionForm()
        context = {'boldmessage':  'Hello, this is the index page',
                   'form': form,
                   'media': ''}
        return render(request, 'aat/home.html', context)


@csrf_exempt
@require_http_methods(['GET'])
#@login_required
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
@require_http_methods(['GET'])
def transcriptionlang(request):

    cmd = ['autosub', '--list-languages']
    try:
        stdout = exec_cmd(cmd)
    except Exception as e:
        log.error(str(e))
        return JsonResponse({'error': 'Cannot retrieve available'
                                      ' languages at that time'})
    if stdout:
        langs = [ l.replace('\t', ', ') for l in stdout.split('\n')[3:]  ]
    else:
        langs = []
    return JsonResponse({"languages": langs})


@csrf_exempt
@require_http_methods(['POST', 'GET'])
#@login_required
def model(request):
    """This method has also to create train YAML files  according to the
    faces uploaded for every recognizer Eighen, Fisher, LBPH """

    if (request.method == 'POST' and
        request.FILES['model']):

        uploadedzip = request.FILES['model']
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

        for type in ['LBPH', 'EF', 'FF']:
            try:
                train(type, uploadedzip.name, extractdir, size)
            except Exception as e:
                log.error(str(e))
                return JsonResponse({'error': 'Cannot train recognizer'})

        # Return faces that recognizer was trained with
        ptrdataqs = RecognizerPreTrainedData.objects.all()
        for o in ptrdataqs:
            if uploadedzip.name.replace('.zip', '') in o.name:
                people = (o.faces).split(', ')

        resp = dict()
        resp['people'] = people

        return JsonResponse(resp)
    else:
        yamls = RecognizerPreTrainedData.objects.all()
        return JsonResponse([y.to_dict() for y in yamls], safe=False)


@csrf_exempt
@require_http_methods(['POST'])
#@login_required
def annotate(request):
    try:
        jsondata = json.loads(request.body)
        schema = {
            "type": "object",
            "properties": {
                "content": { "type": "object",
                    "properties": {
                        "path" : { "type": "string" }
                    }},
                "bounding_boxes": { "type": "string" },
                "recognizer": { "type": "object",
                    "properties": {
                        "name" : { "type": "string" }
                    }},
                "objdetector": { "type": "object",
                    "properties" : {
                        "framerate": { "type": "number" }
                    }},
                "transcription": { "type": "object",
                    "properties": {
                        "input_language": { "type": "string" },
                        "output_language": { "type": "string" }
                    }},
                "cascade": { "type": "object",
                    "properties": {
                        "name": { "type": "array" },
                        "framerate": { "type": "number" },
                        "scale": { "type": "string" },
                        "neighbors": { "type": "string" },
                        "minx": { "type": "string" },
                        "miny": { "type": "string" }
                        }},
                "manual_tags": { "type": "object",
                    "properties": {
                        "frame": { "type": "string" },
                        "position": { "type": "object",
                            "properties": {
                                "xaxis": { "type": "string" },
                                "yaxis": { "type": "string" }
                                }},
                        "dimensions": { "type": "object",
                            "properties": {
                                "width": { "type": "string" },
                                "height": { "type": "string" }
                                }},
                        "class": { "type": "string" }
                        }}
            },
            "required": ["content"],
            "additionalProperties": False
        }
        validate(jsondata, schema)
    except ValueError as error:
        return JsonResponse({'error': 'Bad JSON structure. ' + str(error)})
    except Exception as e:
        return JsonResponse({'error': 'Input JSON is not appropriate'})

    if ('manual_tags' in jsondata.keys()):
        callback = senddata.s(id=jsondata['content']['uid'], manual_tags=jsondata['manual_tags'])
    else:
        callback = senddata.s(id=jsondata['content']['uid'])
    # Transform url video path to local filesystem path
    jsondata['content']['path'] = retrieve_fromurl(jsondata['content']['path'])
    context = process_form(request, jsondata, callback)
    return JsonResponse(context)


@Clock.time
@require_http_methods(['POST', 'GET'])
@login_required
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
                #video_path = get_upload_path(request.FILES['video'], 'No')
                video_path = form.cleaned_data['video']

                jsondata['content'] = dict()
                # URL of the video, in Amazon S3
                jsondata['content']['path'] = retrieve_fromurl(video_path)
                #jsondata['content']['path'] = request.POST['video_dir']

                if (request.POST['detection'] == 'true'):
                    jsondata['cascade'] = dict()
                    jsondata['cascade']['name'] = [1]
                    jsondata['cascade']['scale'] = 1.3
                    jsondata['cascade']['neighbors'] = 5
                    jsondata['cascade']['minx'] = 60
                    jsondata['cascade']['miny'] = 60
                    jsondata['cascade']['framerate'] = 20

                if (request.POST['recognizer'] == 'true'):
                    jsondata['recognizer'] = dict()
                    #jsondata['recognizer']['name'] = 'mecanex_LBPHfaces_model_5.yml'
                    jsondata['recognizer']['name'] = 'Italian_Demo_LBPH.yml'
                if (request.POST['objdetection'] == 'true'):
                    jsondata['objdetector'] = dict()
                    jsondata['objdetector']['name'] = 'SSD_Mobilenet'
                    jsondata['objdetector']['framerate'] = 65
                if (request.POST['transcription'] == 'true'):
                    jsondata['transcription'] = {'input_language': 'en',
                                                 'output_language': 'en'}

                jsondata['bounding_boxes'] = 'True'

            elif(isinstance(form, ComplexDetectionForm)):
                # video_path = get_upload_path(request.FILES['video'],
                #                              request.POST['iszip'])
                video_path = form.cleaned_data['video']

                jsondata['content'] = dict()
                # URL of the video, in Amazon S3 in local filesystem path
                jsondata['content']['path'] = retrieve_fromurl(video_path)

                if (request.POST['detection'] == 'true'):
                    jsondata['cascade'] = dict()
                    jsondata['cascade']['name'] = [1]
                    jsondata['cascade']['scale'] = form.cleaned_data['scale']
                    jsondata['cascade']['neighbors'] = form.cleaned_data['neighbors']
                    jsondata['cascade']['minx'] = form.cleaned_data['min_x_dimension']
                    jsondata['cascade']['miny'] = form.cleaned_data['min_y_dimension']
                    jsondata['cascade']['framerate'] = 10

                if (request.POST['recognizer'] != 'false'):
                    jsondata['recognizer'] = dict()
                    jsondata['recognizer']['name'] = form.cleaned_data['recognizer']
                    jsondata['recognizer']['name'] = form.cleaned_data['face_database']
                if (request.POST['objdetection'] == 'true'):
                    jsondata['objdetector'] = dict()
                    jsondata['objdetector']['name'] = 'SSD_Mobilenet'
                    jsondata['objdetector']['framerate'] = 300
                if (request.POST['transcription'] == 'true'):
                    jsondata['transcription'] = {'input_language': 'en',
                                                 'output_language': 'en'}

                jsondata['bounding_boxes'] = form.cleaned_data['bounding_boxes']

            log.debug('The json created is: ')
            log.debug(jsondata)

            # Callback task
            callback = returnvalues.s(video_path=jsondata['content']['path'])
            context = process_form(request, jsondata, callback)
            if 'error' in context.keys():
                return HttpResponseBadRequest("Error: {}".format(context['error']))
            return render(request, 'aat/home.html', context)
        else:
            log.debug(form.errors.as_data())
            return HttpResponseBadRequest("Please specify the fields missing in the form")
            vidform = formclass()
            return render(request, 'aat/block.html', {'form': vidform})
    else:
        # GET request forwards to CompleDetectionForm
        vidform = ComplexDetectionForm()
        return render(request, 'aat/block.html', {'form': vidform})


def process_form(request, jsondata, callback_task):

    # Create video file
    log.debug('Video local filesystem path is \n{}'.format(jsondata['content']['path']))

    # List of all the annotation to tasks to be excecuted
    header = []
    try:
        names = dict()
        positions = dict()
        objects = dict()
        static_srt = ''

        bounboxes = True
        if ('bounding_boxes' in jsondata.keys()):
            boundboxes = jsondata['bounding_boxes']

        if ('cascade' in jsondata.keys()):

            # Decide the framerate skipping
            framerate = 100
            if 'framerate' in jsondata['cascade'].keys():
                framerate = jsondata['cascade']['framerate']

            # Decide the name skipping
            name = [1]
            if 'name' in jsondata['cascade'].keys():
                name = jsondata['cascade']['name']

            # Decide the scale skipping
            scale = 1.3
            if 'scale' in jsondata['cascade'].keys():
                scale = jsondata['cascade']['scale']

            # Decide the neighbors skipping
            neighbors = 5
            if 'neighbors' in jsondata['cascade'].keys():
                neighbors= jsondata['cascade']['neighbors']

            # Decide the minx skipping
            minx = 30
            if 'minx' in jsondata['cascade'].keys():
                minx = jsondata['cascade']['minx']

            # Decide the miny skipping
            miny = 30
            if 'miny' in jsondata['cascade'].keys():
                miny = jsondata['cascade']['miny']

            # Print values for face detection with Viola-Jones
            log.debug("The values provided are: scale {}, neighbors {},"
                      "min x dimension {}, min y dimension {}"
                      .format(scale, neighbors, minx, miny))

            # Check whether we need recognition
            if 'recognizer' in jsondata.keys():
                # Selected facedb for recognition
                ptrdataqs = RecognizerPreTrainedData.objects.filter(name=jsondata['recognizer']['name'])
                # Recognizer was not found in db
                if ptrdataqs.count() == 0:
                    return {'error': 'The specified recognizer *{}* '
                            'was not found'.format(jsondata['recognizer']['name'])}

                ptrdata = ptrdataqs.last()
                log.debug('Selected recognizer is {}'.format(ptrdata.recognizer))
                log.debug('The faces file has name {}'.format(ptrdata.name))

                recid = ptrdata.name

                log.debug('The faces file has path {}'.format(ptrdata.yml_file.url))
            else:
                recid = ''

            face_task = face_detection_recognition.s(jsondata['content']['path'],
                                                      recid, name, scale,
                                                      neighbors, minx, miny,
                                                      boundboxes, framerate)
            header.append(face_task)

        if('objdetector' in jsondata.keys()):
            framerate = 100
            if 'framerate' in jsondata['objdetector'].keys():
                framerate = jsondata['objdetector']['framerate']

            object_task = object_detection2.s(jsondata['content']['path'], framerate)
            header.append(object_task)

        if ('transcription' in jsondata.keys()):
            inlang = 'en'
            outlang = 'en'
            if ('input_language' in jsondata['transcription'].keys()):
                inlang = jsondata['transcription']['input_language']
            if ('output_language' in jsondata['transcription'].keys()):
                outlang = jsondata['transcription']['output_language']
            log.debug("Host: {}".format(request.get_host()))
            subtitle_task = transcribe.s(jsondata['content']['path'],
                                         inlang, outlang, request.get_host())
            header.append(subtitle_task)
    except Exception as e:
        log.debug(str(e))
        context = {'error': str(e)}
        return context

    if 'senddata' in callback_task.name:
        chord(header)(callback_task)
        return {'message': 'Successfully submitted annotations tasks'}
    else:
        result = chord(header)(callback_task).get()

        # TO TEST
        #if (os.path.exists(result['annotvideopath'])):
        #    shutil.copy(result['annotvideopath'], settings.STATIC_ROOT)
        #    os.remove(result['annotvideopath'])
        # Send all information back to UI

        context = {'form':  DefaultDetectionForm(),
                   'media': os.path.basename(result['annotvideopath']),
                   'faces': result['facedetection'] if 'facedetection' in result.keys() else {},
                   'objects': result['objectdetection'] if 'objectdetection' in result.keys() else {},
                   'srt_file': result['transcription'] if 'transcription' in result.keys() else ""}

    return context


def retrieve_fromurl(url):
    if ('http' in url):
        try:
            import requests
            videopath = os.path.join(settings.S3_ROOT, 'AAT_downloads', url[url.rfind("/")+1:])
            auth_header = {'Authorization': 'Basic QWRtaW5pc3RyYXRvcjpBZG1pbmlzdHJhdG9y'}
            req = requests.get(url, headers=auth_header, stream=True)
            with open(videopath, 'wb') as v:
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                        v.write(chunk)
        except Exception as e:
            log.error(str(e))
            return
    else:
        videopath = url
    return videopath


def get_upload_path(upload, iszip):

    # Handle zip uploaded file
    if (iszip == 'Yes'):
        video_file = extract_video(upload)
        if not os.path.exists(video_file):
            return HttpResponseBadRequest(video_file)

    if isinstance(upload, TemporaryUploadedFile):
        # In most cases execution goes here!
        shutil.move(upload.temporary_file_path(),
                    settings.MEDIA_ROOT)
        video_path = os.path.join(settings.CACHE_ROOT,
                                  os.path.basename(upload.temporary_file_path()))
    else:
        # TODO
        # Have to retrieve the filename from the request.FILES variable
        filename = ''
        video_path = os.path.join(settings.MEDIA_ROOT, filename)
        with open(video_path, 'wb+') as destination:
            for chunk in upload.chunks():
                destination.write(chunk)

    # A filesystem path is returned
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
