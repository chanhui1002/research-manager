#!/usr/bin/env bash
set -e

curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash 2>/dev/null || true
apt-get install -y git-lfs 2>/dev/null || true
git lfs install --skip-smudge 2>/dev/null || true
cd /opt/render/project/src && git lfs pull 2>/dev/null || true

cd /opt/render/project/src/backend
pip install -r requirements.txt
