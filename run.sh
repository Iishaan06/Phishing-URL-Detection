#!/bin/sh
# Simple helper for local development.
set -e

if [ -z "$FLASK_APP" ]; then
  export FLASK_APP=app.main
fi

export FLASK_ENV=development
python -m flask run --host=0.0.0.0 --port=5000

