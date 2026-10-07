#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
HOST="0.0.0.0"
PORT="8050"
URL="http://127.0.0.1:${PORT}/"

cd "$ROOT"
if [[ ! -x "$ROOT/.venv/bin/uvicorn" ]]; then
  python3.12 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -r "$ROOT/backend/requirements.txt"
fi
if [[ ! -f "$ROOT/.env" ]]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
fi

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "端口 ${PORT} 已有服务在跑。"
  echo "请直接浏览器打开：${URL}"
  echo "（若要重启：先关掉占用 ${PORT} 的窗口，再执行 ./start.sh）"
  # 探活
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<PY
import urllib.request
try:
    with urllib.request.urlopen("${URL}api/v1/health", timeout=2) as r:
        print("健康检查：", r.read().decode())
except Exception as e:
    print("健康检查失败：", e)
PY
  fi
  exit 0
fi

echo "正在启动：${URL}"
cd "$ROOT/backend"
exec "$ROOT/.venv/bin/uvicorn" app.main:app --host "$HOST" --port "$PORT"
