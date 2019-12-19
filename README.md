[![GitHub version](https://badge.fury.io/gh/Torniojaws%2Fvortech-backend.svg)](https://badge.fury.io/gh/Torniojaws%2Fvortech-backend)
[![Build Status](https://travis-ci.org/Torniojaws/vortech-backend.svg?branch=master)](https://travis-ci.org/Torniojaws/vortech-backend)
[![Coverage Status](https://coveralls.io/repos/github/Torniojaws/vortech-backend/badge.svg?branch=master)](https://coveralls.io/github/Torniojaws/vortech-backend?branch=master)

# Vortech API

This is the production Rest API of https://www.vortechmusic.com on the new VPS. The frontend is in
the repository: https://github.com/Torniojaws/vortech-front/

## Stack

- **Platform:** Linux, Ubuntu 16.04 64-bit
- **Web server:** Nginx
- **Gateway:** uWSGI
- **Database:** MariaDB
- **Language:** Python 3
- **Framework:** Flask
- **Cache:** Redis
- **Deployment:** Ansible

## Install

You can setup in three different ways, in order of preference:

### Docker Compose

Make sure you have Docker and docker-compose installed, then:

1. `docker-compose up`

### Makefile

The second best method is to use the makefile, which runs a whole slew of Ansible playbooks.

1. Install make: ``sudo apt get install make``
1. Create the file ``deploy/vault_password`` and add the project vault password there.
1. Then in the project root, run ``make deploy-dev`` or ``make deploy-prod``

### Full manual

You can also check the full manual steps from [Install Instructions](INSTALL.md)

## Update

When updating an existing installation, use ``make update-prod``

## Running locally

In the actual server, the backend runs via uWSGI as a service. But locally you can/need to launch
it manually:

1. Start the server: `make run`
1. Send a request, eg. GET http://localhost:5000/api/1.0/news/
1. Create a new User through the register page http://localhost:5000/register
1. To make the user an admin, run this into the DB:
  ``INSERT INTO UsersAccessMapping(UserID, UsersAccessLevelID) VALUES(1, 4);``
   Replace the ``1`` with the actual Users.UserID you have locally. Should usually be ``1``.

## Tests

You can run the tests with ``make test``, or alternatively: ``python3 -m pytest tests/``.
If you want the coverage report when running manually, run it with:
``python3 -m pytest tests/ --cov=apps --cov-report term-missing``

## Versioning

The common ``major.minor.micro`` format is followed. ``major`` releases will be huge updates with
potential breaking features. ``minor`` releases add new features that don't break anything.
``micro`` releases are usually small tweaks and little additions. Until the first production release,
the project stays as ``0.x.x``. The first production release will be ``1.0.0``.
