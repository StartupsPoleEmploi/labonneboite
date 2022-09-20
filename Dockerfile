FROM python:3.6.15-slim-buster
# FROM python:3.10.7-slim-bullseye
# Set timezone
ENV TZ=Europe/Paris
ENV LANG C.UTF-8
# for mysql support & git
RUN apt update && apt install -y \
    git \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    locales \
    # language-pack-fr \
    --no-install-recommends
# switch working directory
WORKDIR /app

RUN mkdir -p /app/logs /app/src /app/jenkins

# install gunicorn
RUN pip install gunicorn

# install dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# import files for finishing (SYTT: Could be done better)
COPY setup* /app/
COPY README.md /app/README.md

COPY ./labonneboite /app/labonneboite
RUN pip install -e .

# running the server
WORKDIR /app/labonneboite

ENV FLASK_APP web.app
# unsupported local error : https://stackoverflow.com/questions/54802935/docker-unsupported-locale-setting-when-running-python-container
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/'        /etc/locale.gen \
    && sed -i -e 's/# fr_FR.UTF-8 UTF-8/fr_FR.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen

RUN flask assets build

# add the entrypoint
COPY alembic.ini /app/labonneboite/
COPY run.sh /app/labonneboite/
RUN chmod +x ./run.sh
ENTRYPOINT ["/bin/bash", "./run.sh"]
