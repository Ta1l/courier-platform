#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /opt/kurer-spb/backups/<snapshot>.db"
  exit 1
fi

SNAPSHOT_PATH="$1"
TARGET_DB="/opt/kurer-spb/tg/applications.db"

if [[ ! -f "${SNAPSHOT_PATH}" ]]; then
  echo "Snapshot not found: ${SNAPSHOT_PATH}"
  exit 1
fi

systemctl stop kurer-api kurer-bot
cp "${SNAPSHOT_PATH}" "${TARGET_DB}"
systemctl start kurer-api kurer-bot

echo "DB restored from ${SNAPSHOT_PATH}"
