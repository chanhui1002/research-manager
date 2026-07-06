#!/usr/bin/env bash
set -e

cd backend
pip install -r requirements.txt

cd ../frontend
npm install
npm run build
