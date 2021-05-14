FROM ubuntu:16.04 AS base
WORKDIR /app
RUN apt-get update -y && apt-get install -y gcc sudo software-properties-common && \
  add-apt-repository ppa:deadsnakes/ppa && \
  apt-get update -y && \
  apt-get install python3.6 -y && \
  update-alternatives --install /usr/bin/python python /usr/bin/python3.6 1 && \
  update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 2

FROM base AS programs
WORKDIR /app
ENV VIRTUAL_ENV=/srv/vortech-backend/venv/
RUN apt-get install -y python3.6-venv python3-setuptools python3-dev python3-pip python3-apt
RUN python3.6 -m venv $VIRTUAL_ENV && \
  . /srv/vortech-backend/venv/bin/activate && \
  python3.6 -m pip install --upgrade pip && \
  python3.6 -m pip install --upgrade virtualenv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
  
FROM programs AS build
WORKDIR /app
RUN . /srv/vortech-backend/venv/bin/activate
RUN python3.6 -m pip install wheel && \
  python3.6 -m pip install setuptools && \
  python3.6 -m pip install setuptools-rust && \
  python3.6 -m pip install ansible
RUN apt-get install python3-apt -y

FROM build AS app
WORKDIR /app
RUN . /srv/vortech-backend/venv/bin/activate
COPY deploy/ ./deploy/
ENV ANSIBLE_CONFIG=deploy/ansible.cfg
ENTRYPOINT ["ansible-playbook", "--connection=local", "deploy/site.yml", "-i", "deploy/inventories/dev"]