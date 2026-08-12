#!/usr/bin/env bash
# Handoff: preflight -> one resumable 0.20.8 pass -> judge.
# Defaults: gpt_low + haiku_low, agent-device only, all Bluesky tasks.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="runner:${PYTHONPATH:-}"
# Shared-machine safety: never permit dedicated-host pattern killing, and never
# inherit ownership claims from an earlier benchmark invocation.
export BENCH_KILL_SCOPE="owned"
export BENCH_PIDS="/tmp/app-control-bench-agent-device-0208.$$.pids.json"
export BENCH_CLONE_PREFIX="${BENCH_CLONE_PREFIX:-bench-ad0208-$$-}"

if [ -n "${BENCH_ENV_FILE:-}" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$BENCH_ENV_FILE"
  set +a
fi

MODELS="${MODELS:-gpt_low,haiku_low}"
APPS="${APPS:-bluesky}"
TASK_ARGS=(); [ -n "${TASK:-}" ] && TASK_ARGS=(--task "$TASK")

BACKEND_PID=""
cleanup_backend() {
  if [ -n "$BACKEND_PID" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup_backend EXIT INT TERM

if [[ ",$APPS," == *,bluesky,* ]] && ! curl -sf -m 2 http://localhost:1987/info >/dev/null; then
  ./start_bluesky_backend.sh > /tmp/app-control-bench-bluesky.log 2>&1 &
  BACKEND_PID=$!
  for _ in $(seq 1 120); do
    curl -sf -m 2 http://localhost:1987/info >/dev/null && break
    kill -0 "$BACKEND_PID" 2>/dev/null || {
      echo "Bluesky backend exited; see /tmp/app-control-bench-bluesky.log" >&2
      exit 1
    }
    sleep 1
  done
  curl -sf -m 2 http://localhost:1987/info >/dev/null || {
    echo "Bluesky backend did not become ready; see /tmp/app-control-bench-bluesky.log" >&2
    exit 1
  }
fi

python3 runner/doctor.py --preflight --models "$MODELS" --tools agent-device --apps "$APPS"
if [ "${PREFLIGHT_ONLY:-0}" = "1" ]; then exit 0; fi
python3 runner/doctor.py --heal --models "$MODELS" --tools agent-device --apps "$APPS"
python3 runner/run_agent_device_refresh.py --models "$MODELS" --apps "$APPS" "${TASK_ARGS[@]}"

if [ "${SKIP_JUDGE:-0}" != "1" ]; then
  CELLS="$(printf '%s' "$MODELS" | sed 's/,/__agent-device,/g')__agent-device"
  python3 runner/judge.py --cell "$CELLS"
fi

python3 runner/doctor.py --models "$MODELS" --tools agent-device --apps "$APPS"

if [ "${REBUILD_SITE:-1}" = "1" ]; then
  (cd ../website && npm ci && npm run build)
fi
