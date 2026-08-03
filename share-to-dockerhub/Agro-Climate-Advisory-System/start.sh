#!/usr/bin/env bash
# =============================================================================
#  start.sh  (Linux / macOS)  —  one-command startup for the reviewer.
#  Brings the DB up first, restores the bundled data, then starts everything.
#  Run from inside the boss-bundle folder:   ./start.sh
# =============================================================================
set -e
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "ERROR: .env is missing next to this script. Ask the sender for it."
  exit 1
fi

echo "[0/6] Downloading images one at a time (~4-5 GB total)..."
# Pulling ONE image at a time (instead of all in parallel) is much gentler on
# unstable/slow connections - Docker Compose's default parallel pull can open
# 6-7 simultaneous downloads, which is enough to trigger TLS handshake timeouts
# on a weak connection. Each image gets its own retries; already-downloaded
# layers are cached, so re-running this never starts over from zero.
IMAGES="donelongo/geonode-app:4.4.2 donelongo/geonode-frontend:latest donelongo/geonode-nginx:1.25.3-latest donelongo/geonode-geoserver:2.24.4-v1 donelongo/geonode-geoserver-data:2.24.4-v1 donelongo/geonode-postgis:15.3-latest memcached:alpine rabbitmq:3-alpine"
failed=""
for img in $IMAGES; do
  echo "   Pulling $img ..."
  ok=0
  for attempt in 1 2 3 4 5; do
    if docker pull "$img"; then ok=1; break; fi
    echo "   Attempt $attempt for $img failed (network hiccup). Retrying in 10s..."
    sleep 10
  done
  if [ "$ok" != "1" ]; then failed="$failed $img"; fi
done
if [ -n "$failed" ]; then
  echo ""
  echo "ERROR: could not download these images after 5 attempts each:$failed"
  echo "This is a network/connectivity issue (e.g. an unstable connection), not a bug in the app."
  echo "Simply run this script again later - images already downloaded are cached and won't restart."
  exit 1
fi
echo "All images downloaded successfully."

echo "[1/6] Starting database only..."
docker compose up -d db

echo "[2/6] Waiting for the database AND its app databases to be ready..."
# The image creates the my_geonode / my_geonode_data databases on first boot via
# an init script. Wait for THOSE to exist, not just for the server to accept
# connections, otherwise the restore runs too early and fails.
until [ "$(docker exec db4my_geonode psql -U postgres -tAc "SELECT count(*) FROM pg_database WHERE datname IN ('my_geonode','my_geonode_data');" 2>/dev/null | tr -d '[:space:]')" = "2" ]; do
  sleep 4
done

echo "[3/6] Restoring databases and granting app-user rights..."
docker cp data/my_geonode.sql       db4my_geonode:/tmp/my_geonode.sql
docker cp data/my_geonode_data.sql  db4my_geonode:/tmp/my_geonode_data.sql
# Restore as the postgres superuser (needed for the PostGIS extension objects)...
docker exec db4my_geonode psql -U postgres -d my_geonode      -f /tmp/my_geonode.sql      >/dev/null
docker exec db4my_geonode psql -U postgres -d my_geonode_data -f /tmp/my_geonode_data.sql >/dev/null
# ...then hand ownership/rights to the app users the app logs in as. Without this,
# the app gets "permission denied" on its own tables and fails to start.
GRANT_SQL() { echo "GRANT ALL ON SCHEMA public TO $1; GRANT ALL ON ALL TABLES IN SCHEMA public TO $1; GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO $1; GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO $1; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $1;"; }
docker exec db4my_geonode psql -U postgres -d my_geonode      -c "$(GRANT_SQL my_geonode)"      >/dev/null
docker exec db4my_geonode psql -U postgres -d my_geonode_data -c "$(GRANT_SQL my_geonode_data)" >/dev/null
echo "   databases restored and permissions granted."

echo "[4/6] Restoring GeoServer config + media into volumes..."
BUNDLE="$(pwd)/data"
docker run --rm -v my_geonode-gsdatadir:/gs -v "$BUNDLE:/bundle" alpine sh -c "cd /gs && tar xzf /bundle/geoserver_data.tar.gz"
docker run --rm -v my_geonode-media:/media  -v "$BUNDLE:/bundle" alpine sh -c "cd /media && tar xzf /bundle/media.tar.gz"

echo "[5/6] Starting the backend (this pulls images the first time)..."
# Bring up django FIRST and wait for it to become healthy. GeoNode's first
# boot takes several minutes; starting everything at once can make dependent
# services give up. We wait here patiently instead.
docker compose up -d db rabbitmq memcached django

echo "Waiting for the backend to finish its first-time setup (this can take 3-8 minutes)..."
dready=0
for i in $(seq 1 60); do
  h=$(docker inspect --format '{{.State.Health.Status}}' django4my_geonode 2>/dev/null)
  if [ "$h" = "healthy" ]; then dready=1; break; fi
  sleep 15
  echo "   ...backend still starting ($((i*15))s, status: $h)"
done
if [ "$dready" != "1" ]; then
  echo "Backend is still not healthy. Last log lines to help diagnose:"
  docker logs django4my_geonode --tail 25
  echo "You can wait a bit longer and re-run 'docker compose up -d', or share these logs."
fi

echo "[6/6] Starting the remaining services (GeoServer, web app)..."
docker compose up -d
sleep 5
docker compose restart geoserver >/dev/null

# The web app is a React dev server; it must COMPILE before it will respond.
echo ""
echo "Waiting for the web app to finish compiling (can take a few minutes)..."
ready=0
for i in $(seq 1 60); do
  if curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000 | grep -q 200; then
    ready=1; break
  fi
  sleep 10
  echo "   ...still compiling ($((i*10))s)"
done

echo ""
if [ "$ready" = "1" ]; then
  echo "======================================================"
  echo "  READY. Open the application in your browser:"
  echo "     ->  http://localhost:3000        <-- THE APP"
  echo "======================================================"
else
  echo "The web app is taking longer than usual to compile."
  echo "Wait 1-2 more minutes, then open http://localhost:3000"
  echo "(If it still won't load, try http://127.0.0.1:3000 instead.)"
fi
echo ""
echo "Other services (optional):"
echo "   GeoNode admin portal :  http://localhost:3500"
echo "   GeoServer            :  http://localhost:8080/geoserver"
