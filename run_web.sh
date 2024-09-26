#!/usr/bin/env bash

# Check if 'venv' directory exists
if [ ! -d "venv" ]; then
    # Create virtual environment
    python3 -m venv venv
fi


# Install packages from requirements.txt
./venv/bin/pip install -r requirements.txt

./venv/bin/python3 web.py