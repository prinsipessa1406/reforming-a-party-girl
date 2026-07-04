#!/bin/bash
cd "$(dirname "$0")"
python3 -c "import flask" 2>/dev/null || python3 -m pip install --quiet flask
python3 editor.py
echo ""
echo "Redigeraren har stängts. Tryck Enter för att stänga det här fönstret."
read
