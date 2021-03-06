FROM opencv

ADD requirements.txt /tmp
ADD requirements.txt .
ADD setup.py .
ADD README.md .

RUN pip install -r /tmp/requirements.txt && \
    find / -name '*.py[co]' -delete

# Add source code
COPY docker /facerec/docker

COPY project /facerec/project

WORKDIR /facerec/project

# Set environmental variables.
ENV DJANGO_SETTINGS_MODULE=opencvFaceRec.settings \
    FACEREC_CONFIG=/facerec/docker/base/config.py \
    FACEREC_DIR=/facerec \
    FACEREC_APP_DIR=/facerec/project \
    FACEREC_MEDIA_DIR=/data/media \
    FACEREC_CACHE_DIR=/data/cache \
    FACEREC_S3_DIR=/data/s3 \
    UWSGI_HTTP_SOCKET=0.0.0.0:8000 \
    UWSGI_PROCESSES=4 \
    CELERY_PROCESSES=4 \
    FACEREC_USER=facerec \
    FACEREC_GROUP=facerec \
    HOME=/home/facerec

# Create non root user and groups.
RUN set -x && \
    groupadd --system --gid 1000 $FACEREC_GROUP && \
    useradd --system --gid $FACEREC_GROUP --uid 1000 -m $FACEREC_USER

# Rename Flat-UI folder
# RUN mv $FACEREC_APP_DIR/aat/static/Flat-UI $FACEREC_APP_DIR/aat/static/flat-ui

# Run link to brainance-ctl.
RUN ln -s $FACEREC_DIR/docker/base/ctl.sh /usr/local/bin/facerec-ctl

# Define volumes.
VOLUME ["$FACEREC_MEDIA_DIR", "$FACEREC_CACHE_DIR"]

# Define entrypoint.
ENTRYPOINT ["/facerec/docker/base/entry.sh"]
