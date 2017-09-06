#!/bin/sh

set -ex

$TOMOTECH_DIR/docker/base/entry.sh

if ! diff -q /tmp/lib-requirements.txt $TOMOTECH_DIR/tomotech-lib/requirements.txt; then
    echo "Pip installing $TOMOTECH_DIR/tomotech-lib"
    pip install -r $TOMOTECH_DIR/tomotech-lib/requirements.txt
    pip install -e $TOMOTECH_DIR/tomotech-lib
fi
if ! diff -q /tmp/web-requirements.txt $TOMOTECH_DIR/requirements.txt; then
    echo "Pip installing $TOMOTECH_DIR"
    pip install -r $TOMOTECH_DIR/requirements.txt
    pip install -e $TOMOTECH_DIR
fi

set +x
echo "Will exec: $@"
exec "$@"
