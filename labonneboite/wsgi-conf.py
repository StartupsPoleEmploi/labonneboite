# Gunicorn configuration file
import multiprocessing  # noqa

bind = "0.0.0.0:8080"
workers = 2
max_requests = 1000
max_requests_jitter = 50

# for dev only
reload = True
reload_engine = "poll"
loglevel = "debug"
# loglevel = "info"
enable_stdio_inheritance = True
