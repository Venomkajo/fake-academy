#!/bin/sh
set -e

# Keep the container's node_modules in sync with package.json.
#
# Why this exists: in dev, docker-compose.override.yml bind-mounts
# ./frontend over /app and hides the host's (empty) node_modules behind a
# named volume. Docker populates that volume from the image ONLY when the
# volume is first created — rebuilding the image after a package.json
# change is not enough: the old volume content sticks around and new
# packages never appear inside the container.
#
# Running `npm install` on every container start fixes that: it is a fast
# no-op when everything is in sync, and installs only what is missing
# after package.json changed.
npm install --no-audit --no-fund

exec "$@"
