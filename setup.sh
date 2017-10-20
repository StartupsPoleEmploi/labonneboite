#! /bin/sh

# FIXME !!?

apt-get update
apt-get --assume-yes install git
apt-get --assume-yes install python
apt-get --assume-yes install python-pip
apt-get --assume-yes install libmariadbclient-dev mariadb-server mariadb-client-core-5.5
apt-get install -qy python-dev
apt-get install -qy libssl-dev
apt-get install -qy libncurses5-dev
apt-get install -qy libhdf5-dev
apt-get install -qy gfortran libopenblas-dev liblapack-dev
