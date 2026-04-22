#!/usr/bin/env bash
# deploy.sh — one-click start/stop for backend (uvicorn) and frontend (static).
#
# Backend  : uvicorn  app.main:app  --host 0.0.0.0 --port ${BACKEND_PORT}
# Frontend : python -m http.server ${FRONTEND_PORT}  (serves frontend/dist)
#
# State is kept in .run/  (PID files + log files). Re-run safely.
#
# Usage:
#   bash scripts/deploy.sh           start   # default
#   bash scripts/deploy.sh start
#   bash scripts/deploy.sh stop
#   bash scripts/deploy.sh restart
#   bash scripts/deploy.sh status
#   bash scripts/deploy.sh logs [backend|frontend]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8042}"
FRONTEND_PORT="${FRONTEND_PORT:-5215}"
ENABLE_FRONTEND_SERVER="${ENABLE_FRONTEND_SERVER:-1}"
RUN_DIR="${PROJECT_ROOT}/.run"
mkdir -p "$RUN_DIR"

BACKEND_PID="${RUN_DIR}/backend.pid"
FRONTEND_PID="${RUN_DIR}/frontend.pid"
BACKEND_LOG="${RUN_DIR}/backend.log"
FRONTEND_LOG="${RUN_DIR}/frontend.log"

log()  { printf '\033[1;34m[deploy]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[deploy]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[deploy]\033[0m %s\n' "$*" >&2; exit 1; }

is_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 1
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

start_backend() {
  if is_running "$BACKEND_PID"; then
    log "backend already running (pid=$(cat "$BACKEND_PID"))"
    return
  fi
  [[ -d .venv ]] || die ".venv not found — run scripts/bootstrap.sh first."

  log "Starting backend on ${BACKEND_HOST}:${BACKEND_PORT} …"
  # shellcheck disable=SC1091
  source .venv/bin/activate
  nohup env APP_HOST="${BACKEND_HOST}" APP_PORT="${BACKEND_PORT}" \
    .venv/bin/uvicorn app.main:app \
      --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" \
      >>"$BACKEND_LOG" 2>&1 &
  echo $! > "$BACKEND_PID"
  sleep 1
  if is_running "$BACKEND_PID"; then
    log "backend pid=$(cat "$BACKEND_PID")  log=${BACKEND_LOG}"
  else
    die "backend failed to start; tail ${BACKEND_LOG}"
  fi
}

start_frontend() {
  if [[ "$ENABLE_FRONTEND_SERVER" == "0" ]]; then
    log "frontend static server disabled (ENABLE_FRONTEND_SERVER=0)"
    return
  fi
  if is_running "$FRONTEND_PID"; then
    log "frontend already running (pid=$(cat "$FRONTEND_PID"))"
    return
  fi
  [[ -d frontend/dist ]] || die "frontend/dist not found — run scripts/bootstrap.sh first."

  log "Serving frontend/dist on :${FRONTEND_PORT} …"
  nohup python3 -m http.server "${FRONTEND_PORT}" \
    --directory frontend/dist --bind 0.0.0.0 \
    >>"$FRONTEND_LOG" 2>&1 &
  echo $! > "$FRONTEND_PID"
  sleep 0.5
  if is_running "$FRONTEND_PID"; then
    log "frontend pid=$(cat "$FRONTEND_PID")  log=${FRONTEND_LOG}"
  else
    die "frontend failed to start; tail ${FRONTEND_LOG}"
  fi
}

stop_one() {
  local name="$1" pid_file="$2"
  if is_running "$pid_file"; then
    local pid; pid="$(cat "$pid_file")"
    log "Stopping ${name} (pid=${pid}) …"
    kill "$pid" 2>/dev/null || true
    for _ in 1 2 3 4 5; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.5
    done
    if kill -0 "$pid" 2>/dev/null; then
      warn "${name} still alive, sending SIGKILL"
      kill -9 "$pid" 2>/dev/null || true
    fi
  else
    log "${name} not running"
  fi
  rm -f "$pid_file"
}

status() {
  for pair in "backend:${BACKEND_PID}:${BACKEND_PORT}" "frontend:${FRONTEND_PID}:${FRONTEND_PORT}"; do
    IFS=: read -r name pid_file port <<<"$pair"
    if is_running "$pid_file"; then
      printf '  %-9s  RUNNING  pid=%-7s  port=%s\n' "$name" "$(cat "$pid_file")" "$port"
    else
      printf '  %-9s  STOPPED                 port=%s\n' "$name" "$port"
    fi
  done
}

logs() {
  local target="${1:-backend}"
  case "$target" in
    backend)  exec tail -n 200 -F "$BACKEND_LOG" ;;
    frontend) exec tail -n 200 -F "$FRONTEND_LOG" ;;
    *) die "logs target must be 'backend' or 'frontend'" ;;
  esac
}

cmd="${1:-start}"
case "$cmd" in
  start)
    start_backend
    start_frontend
    echo
    status
    if [[ "$ENABLE_FRONTEND_SERVER" == "0" ]]; then
      cat <<EOF

Frontend static server: disabled (expected when using Nginx)
Backend bind:           http://${BACKEND_HOST}:${BACKEND_PORT}
Invite codes:           Chrissy, Ethan  (set in the top-right of the UI)

Recommended Nginx setup for this repo:
  listen on :${FRONTEND_PORT}
  serve frontend/dist as static files
  proxy /api/ -> http://127.0.0.1:${BACKEND_PORT}/

If BACKEND_HOST=127.0.0.1, do not open inbound TCP ${BACKEND_PORT}; only open ${FRONTEND_PORT}.
EOF
    else
      cat <<EOF

Open the UI:    http://<server-ip>:${FRONTEND_PORT}
Backend API:    http://<server-ip>:${BACKEND_PORT}/docs
Invite codes:   Chrissy, Ethan  (set in the top-right of the UI)

Make sure your cloud security group allows inbound TCP on ${FRONTEND_PORT} and ${BACKEND_PORT}.
EOF
    fi
    ;;
  stop)
    stop_one frontend "$FRONTEND_PID"
    stop_one backend  "$BACKEND_PID"
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  status)
    status
    ;;
  logs)
    logs "${2:-backend}"
    ;;
  *)
    die "Unknown command: $cmd  (start|stop|restart|status|logs)"
    ;;
esac
