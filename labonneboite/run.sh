# /bin/bash
alembic upgrade head 
gunicorn --config python:wsgi-conf web.app:app