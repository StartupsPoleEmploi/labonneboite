# Docker services

We are currently in the process of migrating external services to docker. This should allow us to:

- run LBB outside of vagrant,
- run external services in containers in production.

Eventually, these instructions will be migrated to the main README. In the
meantime, we draft here the instructions for running additional services in
containers.

## Installing docker and docker-compose


### Ubuntu

Add docker repository:

  sudo apt-get update
  sudo apt-get install -y \
      apt-transport-https \
      ca-certificates \
      curl \
      software-properties-common
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo add-apt-repository \
     "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
     $(lsb_release -cs) \
     stable"
  sudo apt-get update

Install docker:

  sudo apt-get install -y docker-ce

Add user to group:

  sudo usermod -aG docker $USER

Install docker-compose:

  sudo pip install docker-compose


### Mac OS

For other, exotic OS, follow the [Docker manual](https://docs.docker.com/engine/installation/).

## Running services

### Redis

First, create a sentinel.conf file:

    cd redis/
    cp sentinel.conf.orig sentinel.conf

This config file will be modified at runtime. Then, to run a [Redis](http://redis.io/) instance with [Sentinel](https://redis.io/topics/sentinel) support, run:

    docker-compose up

A Redis instance will be running on port 6379 and will be monitored by a Sentinel on port 26379.
