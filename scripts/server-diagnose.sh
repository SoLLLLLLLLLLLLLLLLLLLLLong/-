#!/usr/bin/env bash
set -u

API_URL="${API_URL:-http://127.0.0.1:3000}"
PUBLIC_API_URL="${PUBLIC_API_URL:-http://172.22.121.135:3000}"
WORKER_URL="${WORKER_URL:-http://127.0.0.1:4000}"

echo "== Project =="
pwd

echo
echo "== Package versions =="
node -p "require('./services/api/package.json').version + ' api dev=' + require('./services/api/package.json').scripts.dev" 2>/dev/null || true
node -p "require('./services/avatar-worker/package.json').version + ' worker dev=' + require('./services/avatar-worker/package.json').scripts.dev" 2>/dev/null || true

echo
echo "== Listening ports =="
if command -v ss >/dev/null 2>&1; then
  ss -lntp | grep -E ':(3000|4000)\b' || true
else
  netstat -lntp 2>/dev/null | grep -E ':(3000|4000)\b' || true
fi

echo
echo "== Local health =="
curl -i --max-time 5 "${API_URL}/api/health" || true
echo
curl -i --max-time 5 "${WORKER_URL}/worker/health" || true

echo
echo "== Local image task =="
curl -i --max-time 10 \
  -X POST "${API_URL}/api/image/tasks" \
  -H 'content-type: application/json' \
  -H 'x-user-id: guest-demo' \
  --data '{"prompt":"测试图片","aspectRatio":"1:1"}' || true

echo
echo "== Public API health from server =="
curl -i --max-time 5 "${PUBLIC_API_URL}/api/health" || true

echo
echo "== Nginx/system hints =="
ps -ef | grep -E 'uvicorn|node --watch|nginx|python -m src.main' | grep -v grep || true
