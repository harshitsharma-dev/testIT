#!/bin/bash
# Build script for Render deployment
pip install -r requirements.txt
python -m spacy download en_core_web_sm
