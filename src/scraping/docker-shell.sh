#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Set vairables
export BASE_DIR=$(pwd)
# export PERSISTENT_DIR=$(pwd)/../persistent-folder/
export SECRETS_DIR=$(pwd)/../../../secrets/
export GCP_PROJECT="bloodwise-ai" # CHANGE TO YOUR PROJECT ID
#export GCS_BUCKET_NAME="bloodwise-rag-knowledge-base"
export GCS_BUCKET_NAME="bloodwise-embeddings"
export GOOGLE_APPLICATION_CREDENTIALS="/secrets/llm-service-account.json"
export IMAGE_NAME="llm-scraping"


# Create the network if we don't have it yet
docker network inspect llm-rag-network >/dev/null 2>&1 || docker network create llm-rag-network

# Build the image based on the Dockerfile
docker build -t $IMAGE_NAME -f Dockerfile .

# Run All Containers
# docker compose run --rm --service-ports $IMAGE_NAME

# # Build the image based on the Dockerfile
# docker build -t $IMAGE_NAME -f Dockerfile .

# Run Container
docker run --rm --name $IMAGE_NAME -ti \
-v "$BASE_DIR":/app \
-v "$SECRETS_DIR":/secrets \
-e GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS \
-e GCP_PROJECT=$GCP_PROJECT \
-e GCS_BUCKET_NAME=$GCS_BUCKET_NAME \
$IMAGE_NAME