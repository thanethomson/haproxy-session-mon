#!/usr/bin/env bash
set -e

if [ -z "$1" ]
then
    echo "Usage: ./build-docker-image.sh <docker_image_tag> [<optional_registry_url>]"
    exit 1
fi

# Grab the version number from the Python package
export HAPROXYSM_VERSION=`python -c 'from haproxysessionmon import __version__; print(__version__)'`
echo "Building Docker image $1:$HAPROXYSM_VERSION..."

export IMAGE_FLAGS="-t $1:$HAPROXYSM_VERSION -t $1:latest"

if [ -z "$2" ]
then
    export REGISTRY_TAGS=""
else
    export REGISTRY_TAGS="-t $2/$1:$HAPROXYSM_VERSION -t $2/$1:latest"
fi

docker build $IMAGE_FLAGS $REGISTRY_TAGS .
