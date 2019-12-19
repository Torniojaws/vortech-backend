FROM python:3.7-slim AS platform
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    nginx-full \
    redis-server \
    virtualenv \
    uwsgi \
    uwsgi-emperor \
    uwsgi-plugin-python3 \
    zip

FROM platform AS builder
WORKDIR /app
# Set utf-8 encoding for Python etc
ENV LANG=C.UTF-8
# Do not create .pyc files - not needed in a container
ENV PYTHONDONTWRITEBYTECODE=1
# Speeds up building
ENV PYTHONUNBUFFERED=1
# Use venv python
ENV PATH="/venv/bin:$PATH"
# Setup the virtualenv
RUN python -m venv /venv
RUN pip install --upgrade pip
COPY requirements/prod.txt ./requirements/prod.txt
COPY requirements/dev.txt ./requirements/dev.txt

# Copy requirements and install them separately to use cache effectively
FROM builder AS python-dependencies
ARG BUILD_ENV
ENV BUILD_ENV=${BUILD_ENV}
# dev dependencies are a superset of prod. Only install dev if BUILD_ENV=dev
RUN pip install --no-cache-dir -r requirements/${BUILD_ENV:-prod}.txt

# Setup a clean app container
FROM python-dependencies AS app
COPY --from=python-dependencies /venv /venv
WORKDIR /logs
WORKDIR /app
COPY apps/ ./apps/
COPY settings/ ./settings/
COPY tools/ ./tools/
COPY app.py .
COPY manage.py .
COPY wsgi.py .
COPY config/uwsgi.ini /etc/uwsgi-emperor/vassals/backend.ini
COPY config/nginx-site.conf /etc/nginx/sites-enabled/vortech-backend.conf
