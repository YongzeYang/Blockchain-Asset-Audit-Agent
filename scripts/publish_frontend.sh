#!/usr/bin/env bash
# publish_frontend.sh — copy built frontend assets into an nginx-readable directory.
#
# Default target matches deploy/nginx/blockchain-audit-agent-demo-5215.conf:
#   /var/www/blockchain-audit-agent-demo
#
# Usage:
#   cd /path/to/Blockchain-Asset-Audit-Agent
#   cd frontend && npm run build && cd ..
#   sudo bash scripts/publish_frontend.sh
#
# Optional override:
#   sudo PUBLISH_DIR=/var/www/some-other-dir bash scripts/publish_frontend.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${PROJECT_ROOT}/frontend/dist"
PUBLISH_DIR="${PUBLISH_DIR:-/var/www/blockchain-audit-agent-demo}"

log() { printf '\033[1;34m[publish-frontend]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[publish-frontend]\033[0m %s\n' "$*" >&2; exit 1; }

[[ -d "$SOURCE_DIR" ]] || die "${SOURCE_DIR} not found. Run 'cd frontend && npm run build' first."

mkdir -p "$PUBLISH_DIR"

if command -v rsync >/dev/null 2>&1; then
  log "Syncing ${SOURCE_DIR}/ -> ${PUBLISH_DIR}/ via rsync"
  rsync -a --delete "$SOURCE_DIR/" "$PUBLISH_DIR/"
else
  log "rsync not found; using cp -a"
  find "$PUBLISH_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -a "$SOURCE_DIR/." "$PUBLISH_DIR/"
fi

# Nginx only needs read + execute on directories.
find "$PUBLISH_DIR" -type d -exec chmod 755 {} +
find "$PUBLISH_DIR" -type f -exec chmod 644 {} +

log "Published frontend to ${PUBLISH_DIR}"
log "Point nginx root there, then run: sudo nginx -t && sudo systemctl reload nginx"