FROM producer:latest

ADD entry.sh /facerec/docker/dev/entry.sh

VOLUME $FACEREC_APP_DIR/static

ENTRYPOINT ["/facerec/docker/dev/entry.sh"]
