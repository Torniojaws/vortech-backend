test:
	python3 -m pytest tests/ --cov=apps --cov-report term-missing

deploy:
	# Uncomment if you get GPG errors
	# sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F76221572C52609D
	# sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
	sudo apt install ansible -y
	ansible-playbook deployment/prod.yaml -i localhost, --connection=local --vault-password-file vault_pass.txt

install:
	source ~/.venv/vortech-backend/bin/activate
	pip3 install -r requirements/dev.txt
