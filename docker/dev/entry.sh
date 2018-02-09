#!/bin/sh

set -ex

$FACEREC_DIR/docker/base/entry.sh

if ! diff -q /tmp/requirements.txt $FACEREC_DIR/requirements.txt; then
    echo "Pip installing $FACEREC_DIR"
    pip install -r --ignore-installed $FACEREC_DIR/requirements.txt
    pip install -e $FACEREC_DIR
fi

set +x
echo "Will exec: $@"
exec "$@"
