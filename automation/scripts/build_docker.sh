#!/bin/bash

# Check if DEPLOY_ENVIRONMENT variable is set
if [ -z "$DEPLOY_ENVIRONMENT" ]; then
    # Build Docker image with merge request tag
    TAG="merge_requests"
else
    TAG=$TAG
fi

# cd into ROOT_FOLDER
cd $ROOT_FOLDER

# Log in to the container registry
docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

# Build and tag the Docker image
docker build -t $CI_REGISTRY_IMAGE:$TAG -f docker/Dockerfile .

docker push $CI_REGISTRY_IMAGE:$TAG

cd -
