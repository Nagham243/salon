#!/bin/bash
mkdir -p /app/staticfiles
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn your_project_name.wsgi