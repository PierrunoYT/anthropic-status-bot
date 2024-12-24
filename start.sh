#!/bin/bash

# Ensure script fails on any error
set -e

# Check Python version
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Start the bot
echo "Starting Anthropic Status Bot..."
python run.py