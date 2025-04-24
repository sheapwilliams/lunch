#! /bin/bash

# Create data directory
mkdir -p /data/data
mkdir -p /data/instance
mkdir -p /data/flask_session

# Move lunch_options.json to data directory
mv data/lunch_options.json /data/data/lunch_options.json

uv run gunicorn --bind 0.0.0.0:8000 wsgi:application