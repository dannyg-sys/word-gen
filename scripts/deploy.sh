#!/bin/bash
#
# Deploy word-gen to the production server via rsync over SSH.
#
# The app lives at /opt/word-gen on the remote, runs as the `word-gen` user
# under the systemd unit `word-generator.service`, and is served behind nginx
# at https://word-gen.nellika.io/.
#
# Usage:
#   scripts/deploy.sh              # sync code + restart service
#   scripts/deploy.sh --deps       # also (re)install Python requirements
#   scripts/deploy.sh --dry-run    # show what rsync would do, change nothing
#
# Environment overrides:
#   REMOTE   SSH host alias to deploy to   (default: nell_remote_root)
#   DEST     Remote application directory  (default: /opt/word-gen)
#
set -euo pipefail

REMOTE="${REMOTE:-nell_remote_root}"
DEST="${DEST:-/opt/word-gen}"
SERVICE="word-generator"
APP_USER="word-gen"

# Resolve repo root (parent of this script's directory) and work from there.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

DEPS=0
RSYNC_EXTRA=()
for arg in "$@"; do
    case "$arg" in
        --deps)    DEPS=1 ;;
        --dry-run) RSYNC_EXTRA+=(--dry-run --verbose) ;;
        *) echo "Unknown option: $arg" >&2; exit 1 ;;
    esac
done

VERSION="$(cat VERSION 2>/dev/null || echo unknown)"
echo ">> Deploying word-gen v${VERSION} to ${REMOTE}:${DEST}"

# Sync the application code.
#   --delete removes files on the server that no longer exist in the repo,
#   but the excluded paths below are runtime state and are never touched:
#     data/   -> SQLite db + words list (populated on the server)
#     venv/   -> server-side virtualenv
rsync -az --delete --human-readable "${RSYNC_EXTRA[@]}" \
    --exclude='.git/' \
    --exclude='.github/' \
    --exclude='.claude/' \
    --exclude='venv/' \
    --exclude='scripts/venv/' \
    --exclude='data/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache/' \
    --exclude='.cache/' \
    --exclude='.coverage' \
    --exclude='.DS_Store' \
    ./ "${REMOTE}:${DEST}/"

# Stop here if this was only a preview.
for arg in "$@"; do [ "$arg" = "--dry-run" ] && { echo ">> Dry run complete."; exit 0; }; done

# Fix ownership (rsync ran as root) and finish the deploy on the server.
ssh "${REMOTE}" bash -s -- "${DEST}" "${APP_USER}" "${SERVICE}" "${DEPS}" <<'REMOTE_SCRIPT'
set -euo pipefail
DEST="$1"; APP_USER="$2"; SERVICE="$3"; DEPS="$4"

echo ">> Setting ownership to ${APP_USER}:${APP_USER}"
chown -R "${APP_USER}:${APP_USER}" "${DEST}"

if [ "${DEPS}" = "1" ]; then
    echo ">> Installing Python requirements"
    sudo -u "${APP_USER}" "${DEST}/venv/bin/pip" install --upgrade pip
    sudo -u "${APP_USER}" "${DEST}/venv/bin/pip" install -r "${DEST}/requirements.txt"
fi

# Keep the systemd unit in sync with the repo copy.
if ! cmp -s "${DEST}/word-generator.service" "/etc/systemd/system/${SERVICE}.service"; then
    echo ">> Updating systemd unit"
    cp "${DEST}/word-generator.service" "/etc/systemd/system/${SERVICE}.service"
    systemctl daemon-reload
fi

echo ">> Restarting ${SERVICE}"
systemctl restart "${SERVICE}"
systemctl --no-pager --lines=0 status "${SERVICE}" | head -3
REMOTE_SCRIPT

# Verify the running version through the public endpoint.
echo ">> Verifying deployed version"
sleep 1
DEPLOYED="$(ssh "${REMOTE}" 'curl -fsS http://127.0.0.1:5050/version' 2>/dev/null || echo '{}')"
echo "   local:  ${VERSION}"
echo "   server: ${DEPLOYED}"
echo ">> Done. https://word-gen.nellika.io/"
