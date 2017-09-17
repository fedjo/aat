"""
Django settings for opencvFaceRec project.

Generated by 'django-admin startproject' using Django 1.9.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import sys
import glob

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'z$$g)$at(u&m$^pet8x!$xd--ly6g7&^s%*v2a!$72*@9e1s&!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'revproxy',
    'thesis'
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

ROOT_URLCONF = 'opencvFaceRec.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'opencvFaceRec.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db/db.sqlite3'),
        'NAME': '/data/db/db.sqlite3',
    }
}

# Logging configuration

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'thesis': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Media files (uploads and generated files stored in models)

MEDIA_ROOT = os.path.join(BASE_DIR, 'data/')


# Tomotech cache directory

CACHE_ROOT = os.path.join(BASE_DIR, 'cache/')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
#STATICFILES_DIRS = (
        #os.path.join(BASE_DIR, 'static'),
        #)

# Celery configuration

CELERY_SETTINGS = {
    'BROKER_URL': 'amqp://guest@127.0.0.1/',
    'CELERYD_CONCURRENCY': 4,
    'CELERY_RESULT_BACKEND': 'amqp',
    # 'CELERY_RESULT_SERIALIZER': 'json',
    'CELERY_TASK_SERIALIZER': 'json',
    'CELERYD_PREFETCH_MULTIPLIER': 1,
    # 'CELERYD_MAX_TASKS_PER_CHILD': 1,
    #'CELERYD_TASK_TIME_LIMIT': 60 * 10,
    #'CELERYD_TASK_SOFT_TIME_LIMIT': 60 * 8,
    #'CELERY_ALWAYS_EAGER': True,
}

# Override configuration with files that extend this one in local_settings/

def get_conf_files():
    config = os.getenv('FACEREC_CONFIG')
    files = []
    if config:
        if not os.path.exists(config):
            raise Exception("Env var FACEREC_CONFIG points to '%s', "
                            "but path doesn't exist." % config)
    else:
        config = os.path.join(BASE_DIR, 'conf.d')
    if os.path.isdir(config):
        files = glob.glob(os.path.join(config, '[a-zA-Z0-9]*.py'))
    elif os.path.isfile(config):
        files = [config]
    else:
        files = []
    print >> sys.stderr, "Will load configuration from files:", files
    return files

print >> sys.stderr, "Will execfile now!"
map(execfile, get_conf_files())

