#!/bin/bash

# Create a 32x32 transparent PNG with a green circle and white text
convert -size 32x32 xc:transparent \
  -fill '#9ED66F' -draw 'circle 16,16 16,0' \
  -fill white -pointsize 12 -font Arial-Bold -gravity center -annotate +0+0 "now" \
  -background transparent \
  static/favicon.ico 