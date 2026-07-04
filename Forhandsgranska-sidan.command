#!/bin/bash
cd "$(dirname "$0")"
PORT=8888
python3 -m http.server "$PORT" > /dev/null 2>&1 &
SERVER_PID=$!
sleep 1
open "http://localhost:$PORT"
echo ""
echo "Sidan förhandsgranskas nu på http://localhost:$PORT"
echo "Gjorde du en ändring? Kör om build.py (eller spara i redigeraren) och tryck sen"
echo "Cmd+R i webbläsarfliken för att se den nya versionen."
echo ""
echo "Tryck Enter här i Terminal-fönstret när du är klar för att stänga förhandsgranskningen."
read
kill "$SERVER_PID" 2>/dev/null
