[![GitHub version](https://badge.fury.io/gh/Torniojaws%2Fvortech-backend.svg)](https://badge.fury.io/gh/Torniojaws%2Fvortech-backend)
[![Build Status](https://travis-ci.org/Torniojaws/vortech-backend.svg?branch=master)](https://travis-ci.org/Torniojaws/vortech-backend)
[![Coverage Status](https://coveralls.io/repos/github/Torniojaws/vortech-backend/badge.svg?branch=master)](https://coveralls.io/github/Torniojaws/vortech-backend?branch=master)

# Vortech API

This will be the production API on the new VPS and will be used in the future version of
https://www.vortechmusic.com as the RESTful API for use by the frontend that will be done in a
separate repository, most likely using Vue.js due to the recent React licensing developments.

## Stack

- **Platform:** Linux, Ubuntu 16.04 64-bit
- **Web server:** Nginx
- **Gateway:** uWSGI
- **Database:** MariaDB
- **Language:** Python 3
- **Framework:** Flask

## Install

See the [Install Instructions](INSTALL.md)

## Tests

You can run the tests with ``python3 -m pytest tests/``. If you want the coverage report too, run
it with: ``python3 -m pytest --cov-report= --cov=apps tests/``

## Versioning

The common ``major.minor.micro`` format is followed. ``major`` releases will be huge updates with
potential breaking features. ``minor`` releases add new features that don't break anything.
``micro`` releases are usually small tweaks and little additions. Until the first production release,
the project stays as ``0.x.x``. The first production release will be ``1.0.0``.
