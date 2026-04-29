#!/bin/bash
set -e

# Docker named volumes initialize as root:root. Fix ownership of /data so the
# lunch user can create subdirectories and write the database. This runs once
# as root on every container start, then we drop privileges immediately.
chown lunch:lunch /data

exec gosu lunch "$@"
