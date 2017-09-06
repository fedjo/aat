#!/usr/bin/env bash

# Exit with error if any command returns non zero code.
set -e
# Exit with error if any undefined variable is referenced.
set -u


DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )
PULL=

USAGE="Usage: $0 [options] <version>

Options:
    -h          Display this help message.
    -p          Pull base image before building.

Positional arguments:
    <version>   Version of software (probably branch/tag name or commit sha).
                This is used as the image tag.
"

log() { echo "$@" >&2; }

while getopts "hp" opt; do
    case "$opt" in
        h)
            echo "$USAGE"
            exit
            ;;
        p)
            PULL=1
            ;;
        \?)
            log "$USAGE"
            log
            log "ERROR: Invalid option: -$OPTARG"
            exit 1
    esac
done
shift $((OPTIND-1))

if [ "$#" -eq 0 ]; then
    log "$USAGE"
    log
    log "ERROR: No version/tag specified."
    exit 1
fi
if [ "$#" -gt 1 ]; then
    log "$USAGE"
    log
    log "ERROR: Multiple version/tag specified."
    exit 1
fi
TAG=$1

if [ -z "$PULL" ]; then
    BUILD_ARGS=""
else
    BUILD_ARGS="--pull"
fi

DEPS_IMG="opencv:$TAG"
WEB_IMG="producer:$TAG"
DEV_IMG="producer/dev:$TAG"

log "Will build images"
log "deps:              $DEPS_IMG"
log "web:               $WEB_IMG"
log "dev:               $DEV_IMG"
log
log

log "Building deps (opencv) image"
log
set -x
docker build $BUILD_ARGS -t $DEPS_IMG \
    -f $DIR/docker/base/Dockerfile $DIR
set +x
log
log

log "Building web (producer) base image"
log
set -x
sed -E "s|^FROM .+$|FROM $DEPS_IMG|" $DIR/docker/web/Dockerfile \
    > $DIR/docker/web/Dockerfile.tmp
docker build -t $WEB_IMG -f $DIR/docker/web/Dockerfile.tmp $DIR
set +x
log
log

log "Building dev (producer-dev) image"
log
set -x
sed -E "s|^FROM .+$|FROM $WEB_IMG|" $DIR/docker/dev/Dockerfile \
    > $DIR/docker/dev/Dockerfile.tmp
docker build -t $DEV_IMG -f $DIR/docker/dev/Dockerfile.tmp $DIR/docker/dev
set +x
log
log

log "Building nginx image with static files"
log
set -x
docker run --rm \
    -v $DIR/docker/nginx/static:/tomotech-web/tomotech/web/static \
    $WEB_IMG \
    /tomotech-web/tomotech/web/manage.py collectstatic --noinput
docker build $BUILD_ARGS -t $NGINX_IMG $DIR/docker/nginx
docker run --rm -v $DIR/docker/nginx/:/mnt/nginx $WEB_IMG \
    rm -rf /mnt/nginx/static
set +x
log
log

log "Built images"
log
log "deps:              $DEPS_IMG"
log "web:               $WEB_IMG"
log "dev:               $DEV_IMG"
log "nginx:             $NGINX_IMG"
