#!/usr/bin/env bash
set -euo pipefail

if [ -f /opt/airflow/requirements.txt ]; then
  pip install --no-cache-dir -r /opt/airflow/requirements.txt || true
fi

airflow db upgrade

exec airflow "$@"
