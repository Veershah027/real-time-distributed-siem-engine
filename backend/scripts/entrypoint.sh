#!/usr/bin/env sh
set -eu

ROLE="${1:-api}"

wait_for() {
  host="$1"; port="$2"; name="$3"; tries=60
  echo "waiting for ${name} at ${host}:${port} ..."
  while [ "$tries" -gt 0 ]; do
    if python -c "import socket,sys; s=socket.socket(); s.settimeout(2); sys.exit(0 if s.connect_ex((sys.argv[1], int(sys.argv[2])))==0 else 1)" "$host" "$port" 2>/dev/null; then
      echo "${name} is up"; return 0
    fi
    tries=$((tries - 1)); sleep 1
  done
  echo "timed out waiting for ${name}" >&2; return 1
}

wait_for "${POSTGRES_HOST:-postgres}" "${POSTGRES_PORT:-5432}" postgres
wait_for "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}" redis

case "$ROLE" in
  api)
    echo "running migrations ..."
    alembic upgrade head
    python -m app.seed
    exec uvicorn app.main:app --host "${SIEM_API_HOST:-0.0.0.0}" --port "${SIEM_API_PORT:-8000}" \
      --proxy-headers --forwarded-allow-ips="*" --no-server-header
    ;;
  worker)
    sleep 6
    exec python -m app.worker
    ;;
  *)
    echo "unknown role: $ROLE" >&2; exit 1
    ;;
esac
