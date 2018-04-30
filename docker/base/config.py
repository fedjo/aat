CELERY_SETTINGS['BROKER_URL'] = 'amqp://guest@rabbitmq/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db/db.sqlite3'),
        'NAME': '/data/db/db.sqlite3',
    }
}

MEDIA_ROOT = os.getenv('FACEREC_MEDIA_DIR', MEDIA_ROOT)

CACHE_ROOT = os.getenv('FACEREC_CACHE_DIR', CACHE_ROOT)

S3_ROOT = os.getenv('FACEREC_S3_DIR', S3_ROOT)
