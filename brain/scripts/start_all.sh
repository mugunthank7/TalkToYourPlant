#!/usr/bin/env bash
# Start the whole stack locally. Logs go to brain/eval/status/*.log. Stop with brain/scripts/stop_all.sh
#   :8000 engine (M)   :8100 brain chat API (live engine)   :8200 run dashboard   :8300 integration monitor   :5180 3D twin
set -u
cd "$(dirname "$0")/../.."
L=brain/eval/status; mkdir -p "$L"
if [ ! -x sim/.venv/bin/uvicorn ]; then
  echo "engine venv missing: python3 -m venv sim/.venv && for p in \$(grep -v '^#' sim/requirements.txt | sed 's/\[.*//'); do sim/.venv/bin/pip install \"\$p\"; done"
  echo "(install packages one by one if the network is flaky; a single bulk install failed here with DNS errors)"; exit 1
fi
(cd sim && ../sim/.venv/bin/uvicorn plantsim.api:app --port 8000 > "../$L/engine.log" 2>&1 &)
sleep 12
(SIM_MODE=live SIM_URL=http://localhost:8000 python3 brain/app/api.py > "$L/api.log" 2>&1 &)
(python3 brain/app/dashboard.py > "$L/dash.out" 2>&1 &)
(python3 brain/app/monitor.py > "$L/monitor.log" 2>&1 &)
if [ -d twin/node_modules ]; then (cd twin && npm run dev > "../$L/twin.log" 2>&1 &); else echo "twin deps missing: cd twin && npm install"; fi
sleep 15
echo "engine    http://localhost:8000/health"
echo "chat      http://localhost:8100"
echo "runs      http://localhost:8200"
echo "monitor   http://localhost:8300"
echo "3D twin   http://localhost:5180   (click a station)"
