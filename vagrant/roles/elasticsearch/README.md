Ansible ElasticSearch playbook [![Build Status](https://travis-ci.org/deimosfr/ansible-elasticsearch.svg?branch=master)](https://travis-ci.org/deimosfr/ansible-elasticsearch)
=====

This role installs and configures ElasticSearch on a server.

Requirements
------------

This role requires Ansible 1.4 or higher and platform requirements are listed
in the metadata file.

Role Variables
--------------

The variables that can be passed to this role and a brief description about
them are as follows.

```yaml
# ES v2
es_version: "2.x"
#es_version: "1.7"
es_apt_gpg_url: "https://packages.elastic.co/GPG-KEY-elasticsearch"
es_apt_repo: "deb https://packages.elasticsearch.org/elasticsearch/{{es_version}}/debian stable main"

# Java
es_install_java: True
es_java_version: "openjdk-8-jdk"

es_fqdn: localhost
es_port: 9200

# Force user ids
es_uid:
es_gid:

# Manage service
es_manage_service: True
es_start_options:
   ES_HEAP_SIZE: "2g"

# Configuration file
es_config_file:

# Install plugins
es_install_plugins:
  - name: head
    path: mobz/elasticsearch-head
  - name: kopf
    path: lmenezes/elasticsearch-kopf
  - name: HQ
    path: royrusso/elasticsearch-HQ
  - name: marvel
    path: elasticsearch/marvel/latest

# Curator tool
es_install_curator: False
```

Examples
========

```yaml
# Roles
- name: log server
  hosts: logs
  user: root
  roles:
    - deimosfr.elasticsearch
  vars_files:
    - "host_vars/elasticsearch.yml"

```

Dependencies
------------

None

License
-------

GPL

Author Information
------------------

Pierre Mavro / deimosfr
