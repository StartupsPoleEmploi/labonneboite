FROM python:3.10.7-slim-bullseye


# Set timezone
ENV TZ=Europe/Paris
ENV FLASK_APP web.app

# for mysql support & git & french langage support
RUN apt-get update && apt-get install -y \
    git \
    python3-dev \
    default-mysql-client \
    default-libmysqlclient-dev \
    build-essential \
    locales \
    --no-install-recommends

# switch working directory
WORKDIR /app
RUN mkdir -p /app/logs

# Installing requirements
COPY pyproject.toml /app/
COPY poetry.lock /app/
COPY setup.cfg /app/
COPY README.md /app/

# File imports : source code
COPY ./labonneboite /app/labonneboite
RUN pip install poetry \ 
    && poetry install

WORKDIR /app/labonneboite

# This is a folder to place sql files that will be imported directly after running alembic and before the create index script
RUN mkdir /app/labonneboite/sql

# unsupported local error : https://stackoverflow.com/questions/54802935/docker-unsupported-locale-setting-when-running-python-container
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/'        /etc/locale.gen \
    && sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen

# building flask assets
RUN poetry run flask assets build

# activate entrypoints
RUN chmod +x -R ./entrypoints/

# default entry point is run
ENTRYPOINT ["/bin/bash", "./entrypoints/run.sh"]
