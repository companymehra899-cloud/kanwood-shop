#!/bin/bash
cd "$(dirname "$0")"
python3 -m pip install --break-system-packages -q -r requirements.txt
exec python3 app.py
