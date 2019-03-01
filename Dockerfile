FROM ubuntu:18.04

# Set timezone
ENV TZ=Europe/Paris

# Install system requirements
ENV LANG C.UTF-8
RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt install -y \
        git \
        libmysqlclient-dev \
        # install mysqldump required by the importer
        mysql-client \
        language-pack-fr \
        python3 python3-dev python3-pip \
        tzdata \
        # scipy
        gfortran libblas-dev liblapack-dev libatlas-base-dev \
    && pip3 install virtualenv

# Install python requirements
RUN mkdir -p /labonneboite/logs /labonneboite/src /labonneboite/jenkins
WORKDIR /labonneboite/src
COPY requirements.txt .
RUN virtualenv ../env && \
    ../env/bin/pip install -r requirements.txt

# Copy and install code
COPY . /labonneboite/src
RUN git clean -xfd
RUN ../env/bin/pip install -e .

# Generate static assets
ENV FLASK_APP labonneboite.web.app
RUN ../env/bin/flask assets build

# Run uwsgi
EXPOSE 8000
CMD ["../env/bin/uwsgi", "./docker/uwsgi.ini"]
