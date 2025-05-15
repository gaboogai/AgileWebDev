#!/bin/bash

pkill -f "flask run" || true

export FLASK_APP=server.py
export FLASK_ENV=testing
export SECRET_KEY=testing_secret_key

pip install -r requirements.txt
pip install pytest selenium webdriver-manager

python -c "from app import db; db.create_all()"

python -m pytest -v

echo "Tests completed!"