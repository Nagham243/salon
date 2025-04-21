#!/bin/bash
mkdir -p /app/staticfiles
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn sportclub.wsgi