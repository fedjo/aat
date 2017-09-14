#!/bin/sh

set -e

_preinit() {
    $FACEREC_APP_DIR/manage.py migrate --no-input
}

_postinit() {
    #$FACEREC_APP_DIR/manage.py addexam 'Demo Exam' clinical_fmri.zip -s3
    cp -r $FACEREC_APP_DIR/static/haar_cascades $FACEREC_MEDIA_DIR
    cp -r $FACEREC_APP_DIR/static/recognizer_train_data $FACEREC_MEDIA_DIR
    $FACEREC_APP_DIR/manage.py loaddata prepop
    echo ""
}

prodinit() {
    set -x
    _preinit
    if [ -n "$FACEREC_ADMIN_USER" ] && [ -n "$FACEREC_ADMIN_PASSWORD" ]; then
        $FACEREC_APP_DIR/manage.py autosuperuser \
            $FACEREC_ADMIN_USER $FACEREC_ADMIN_PASSWORD
    fi
    _postinit
}

devinit() {
    set -x
    _preinit
    $FACEREC_APP_DIR/manage.py collectstatic --no-input
    $FACEREC_APP_DIR/manage.py autosuperuser
    _postinit
}

run_uwsgi() {
    set -x
    exec uwsgi \
        --module opencvFaceRec.wsgi \
        --chdir $FACEREC_APP_DIR \
        --http-socket $UWSGI_HTTP_SOCKET \
        --master \
        --processes $UWSGI_PROCESSES \
        --uid $FACEREC_USER \
        --gid $FACEREC_GROUP \
        --vacuum \
        --buffer-size 65535 \
        $@
}

run_celery() {
    set -x
    exec celery worker \
        --app opencvFaceRec \
        --workdir $FACEREC_APP_DIR \
        --uid $FACEREC_USER \
        --gid $FACEREC_GROUP \
        --concurrency $CELERY_PROCESSES \
        -O fair \
        $@
}


SELF="$0"

USAGE="$SELF <command>

Main entrypoint for operations and processes of FACEREC inside docker
container.

Commands:
    init <profile>  Set up environment according to <profile>. Possible values
                    for profile are:
                        dev:
                            - apply migrations
                            - collect django static files
                            - autocreate admin user with admin password
                            - download atlas
                            - create client CA
                            - create server CA
                            - create dcm2web Cert
                            - add demo exam
                        prod:
                            - apply migrations
                            - autocreate admin user with name and password
                              taken from environmnetal variables, if set
                            - download atlas
                            - create client CA
                            - create server CA
                            - create dcm2web Cert
                            - add demo exam
                files, create admin user etc.
    celery          Start celery worker, using exec to substitute current process.
    uwsgi           Start uwsgi server, using exec to substitute current process.
    help            Display this help message.

"

CMD="$1"
if [ -n "$CMD" ]; then
    shift
fi

case "$CMD" in
    init)
        if [ "$1" = "dev" ]; then
            devinit
        elif [ "$1" = "prod" ]; then
            prodinit
        elif [ -z "$1" ]; then
            echo "No init profile specified." >&2
            exit 1
        else
            echo "Invalid init profile specified." >&2
            exit 1
        fi
        ;;
    uwsgi)
        run_uwsgi $@
        ;;
    celery)
        run_celery $@
        ;;
    help|--help|-h)
        echo "$USAGE"
        ;;
    *)
        echo "$USAGE" >&2
        echo "Wrong invocation." >&2
        exit 1
        ;;
esac
