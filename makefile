test:
	python3 -m pytest tests/ --cov=apps --cov-report term-missing

install:
	source ~/.venv/vortech-backend/bin/activate
	pip3 install -r requirements/dev.txt
