test:
	python3 -m pytest tests/ --cov=apps --cov-report term-missing

# Run these if you get GPG errors during deploy-dev or deploy-prod
# sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F76221572C52609D
# sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D

deploy-dev:
	export ANSIBLE_CONFIG=deploy/ansible.cfg && ansible-playbook --ask-become-pass --connection=local deploy/site.yml -i deploy/inventories/dev

deploy-prod:
	export ANSIBLE_CONFIG=deploy/ansible.cfg && ansible-playbook --ask-become-pass --connection=local deploy/site.yml -i deploy/inventories/prod

install:
	source ~/.venv/vortech-backend/bin/activate
	pip3 install -r requirements/dev.txt
