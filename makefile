SHELL := /bin/bash

test:
	python3 -m flake8
	python3 -m pytest tests/ --cov=apps --cov-report term-missing

# Run these if you get GPG errors during deploy-dev or deploy-prod
# sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F76221572C52609D
# sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D

deploy-dev:
	-deactivate  # In case a virtualenv is active
	sudo apt install python3-pip
	sudo -H pip3 install wheel
	sudo -H pip3 install ansible  # This will install the latest Ansible globally
	export ANSIBLE_CONFIG=deploy/ansible.cfg && ansible-playbook --ask-become-pass --connection=local deploy/site.yml -i deploy/inventories/dev

deploy-prod:
	-deactivate # In case a virtualenv is active
	sudo apt install python3-pip
	sudo -H pip3 install wheel
	sudo -H pip3 install ansible
	export ANSIBLE_CONFIG=deploy/ansible.cfg && ansible-playbook --ask-become-pass --connection=local deploy/site.yml -i deploy/inventories/prod

run:
	source ~/.venv/vortech-backend/bin/activate
	pip3 install -r requirements/dev.txt
	python3 manage.py runserver -h 0.0.0.0

update-prod:
	sudo apt update
	sudo apt upgrade
	sudo apt autoremove
	sudo git checkout master
	sudo git pull
	source /srv/vortech-backend/venv/bin/activate; \
	pip3 install -r requirements/prod.txt; \
	python3 manage.py db upgrade
	sudo touch --no-dereference /etc/uwsgi-emperor/vassals/vortech-backend.ini
	echo "Update done!"
