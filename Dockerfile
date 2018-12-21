FROM ubuntu:18.04

# Install system requirements
ENV LANG C.UTF-8
RUN apt update && \
    apt install -y \
        git \
        libmysqlclient-dev \
        language-pack-fr \
        python3 python3-dev python3-pip \
        # scipy
        gfortran libblas-dev liblapack-dev libatlas-base-dev \
    && pip3 install virtualenv

# Install python requirements
RUN mkdir -p /labonneboite/logs /labonneboite/src
WORKDIR /labonneboite/src
COPY requirements.txt .
RUN virtualenv ../env && \
    ../env/bin/pip install -r requirements.txt

# Copy and install code
COPY . /labonneboite/src
RUN git clean -xfd
RUN ../env/bin/pip install -e .

# Run uwsgi
EXPOSE 8000
CMD ["../env/bin/uwsgi", "./docker/uwsgi.ini"]
