# /bin/bash
alembic upgrade head 

gunicorn --workers 2 --bind 0.0.0.0:8080 web.app:app