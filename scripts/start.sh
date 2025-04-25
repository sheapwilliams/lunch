#!/bin/bash

# Parse command line arguments
while getopts "p" opt; do
  case $opt in
    p)
      ENV_FILE=".env-prod"
      IS_PROD=true
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Default to test environment if -p not specified
if [ -z "$IS_PROD" ]; then
    ENV_FILE=".env-test"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                        ⚠️  WARNING ⚠️                          ║"
    echo "║                                                                ║"
    echo "║              Running in TEST environment mode!                 ║"
    echo "║        Use -p flag to run in production environment            ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo
fi

docker run \
    --init \
    -p 8000:8000 \
    --env-file $ENV_FILE \
    --mount type=volume,source=lunch,target=/data \
    lunch:latest
