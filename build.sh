#!/usr/bin/env bash
set -e

cd backend
pip install -r requirements.txt
echo "Build complete. DB exists: $(ls -la research_manager.db 2>&1)"
