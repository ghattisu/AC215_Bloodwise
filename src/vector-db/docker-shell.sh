#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

# Set vairables
export BASE_DIR=$(pwd)
export SECRETS_DIR=$(pwd)/../secrets/
export GCP_PROJECT="bloodwise-ai" # CHANGE TO YOUR PROJECT ID
export GOOGLE_APPLICATION_CREDENTIALS="/secrets/llm-service-account.json"
export IMAGE_NAME="bloodwise-vector-db-cli"

# Create the network if we don't have it yet
docker network inspect bloodwise-network >/dev/null 2>&1 || docker network create bloodwise-network

# Build the image based on the Dockerfile
docker build -t $IMAGE_NAME -f Dockerfile .

# Run All Containers
docker-compose run --rm --service-ports $IMAGE_NAME