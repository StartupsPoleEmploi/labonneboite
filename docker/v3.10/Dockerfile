FROM python:3.10.7-slim-bullseye

# Set timezone
ENV TZ=Europe/Paris
ENV FLASK_APP web.app

ENV PYTHONUNBUFFERED=TRUE

# for mysql support & git & french langage support
RUN apt-get update && apt-get install -y \
    git \
    curl \
    python3-dev \
    default-mysql-client \
    default-libmysqlclient-dev \
    build-essential \
    locales \
    --no-install-recommends

WORKDIR /app

# File imports : requirements
COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml

RUN pip install poetry \ 
    && poetry install --no-root

# File imports : source code
COPY . .

# This is a folder to place sql files that will be imported directly after running alembic and before the create index script
RUN mkdir -p /sql

# same for logs
RUN mkdir -p /app/logs

# unsupported local error : https://stackoverflow.com/questions/54802935/docker-unsupported-locale-setting-when-running-python-container
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/'        /etc/locale.gen \
    && sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen

# building flask assets
RUN cd labonneboite && poetry run flask assets build

# activate entrypoints
COPY ./docker/v3.10/entrypoints /entrypoints
RUN chmod +x -R /entrypoints/

# default entry point is run
ENTRYPOINT ["/bin/bash", "/entrypoints/run.sh"]
