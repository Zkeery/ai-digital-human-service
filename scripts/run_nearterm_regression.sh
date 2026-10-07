#!/usr/bin/env bash
# 近程本地加固：一键跑 A1～C2 相关后端门禁＋前端单测（不上线）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "缺少虚拟环境：${ROOT}/.venv  （先执行 ./start.sh 或 python3.12 -m venv .venv）"
  exit 1
fi

echo "== 后端近程门禁（stage39～43）=="
"$PY" -m pytest \
  backend/tests/test_stage39_multi_entry.py \
  backend/tests/test_stage40_entry_agent_gate.py \
  backend/tests/test_stage41_lab_stats.py \
  backend/tests/test_stage42_rag_pilot.py \
  backend/tests/test_stage43_rag_gate.py \
  -q --tb=line

echo "== 前端单测 =="
(
  cd frontend
  npm test -- --run
)

echo "== 近程回归通过 =="
echo "可选手测清单：docs/MVP/产品走查清单.md （含近程 N1～N16：入口／统计／RAG／口播／信用卡／账户／转账／银行卡／登录密码／投诉／本地动效）"
