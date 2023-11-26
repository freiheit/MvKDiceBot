#!/bin/sh

if which yum; then
  sudo yum --skip-broken -y install python3.11 python3.11-devel python3.11-pip python3.11-pip-wheel python3.11-wheel
fi
# TODO: elif apt ...

python3.11 -m venv --symlinks --system-site-packages .venv
./.venv/bin/pip install -r requirements.txt
