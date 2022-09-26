FROM python:3.6.15-slim-buster

# Set timezone
ENV TZ=Europe/Paris
ENV FLASK_APP web.app

# for mysql support & git & french langage support
RUN apt update && apt install -y \
    git \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    locales \
    --no-install-recommends

# switch working directory
WORKDIR /app
RUN mkdir -p /app/logs

# Installing requirements
# COPY docker/v3.6/requirements.txt /requirements.txt
# RUN pip install -r /requirements.txt

# File imports : source code
COPY docker/v3.6/ /app/
COPY ./labonneboite /app/labonneboite
RUN pip install -e .
WORKDIR /app/labonneboite

# unsupported local error : https://stackoverflow.com/questions/54802935/docker-unsupported-locale-setting-when-running-python-container
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/'        /etc/locale.gen \
    && sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen

# building flask assets
RUN flask assets build

# add the entrypoint
RUN chmod +x ./run.sh

ENTRYPOINT ["/bin/bash", "./run.sh"]
