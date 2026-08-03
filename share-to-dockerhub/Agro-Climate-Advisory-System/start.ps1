# =============================================================================
#  start.ps1  (Windows / PowerShell)  -  one-command startup for the reviewer.
#  Brings the DB up first, restores the bundled data, then starts everything.
#  Run from inside the boss-bundle folder:   .\start.ps1
# =============================================================================
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env is missing next to this script. Ask the sender for it." -ForegroundColor Red
    exit 1
}

Write-Host "[0/6] Downloading images one at a time (~4-5 GB total)..." -ForegroundColor Green
# Pulling ONE image at a time (instead of all in parallel) is much gentler on
# unstable/slow connections - Docker Compose's default parallel pull can open
# 6-7 simultaneous downloads, which is enough to trigger TLS handshake timeouts
# on a weak connection. Each image gets its own retries; already-downloaded
# layers are cached, so re-running this never starts over from zero.
$images = @(
    "donelongo/geonode-app:4.4.2",
    "donelongo/geonode-frontend:latest",
    "donelongo/geonode-nginx:1.25.3-latest",
    "donelongo/geonode-geoserver:2.24.4-v1",
    "donelongo/geonode-geoserver-data:2.24.4-v1",
    "donelongo/geonode-postgis:15.3-latest",
    "memcached:alpine",
    "rabbitmq:3-alpine"
)
$failed = @()
foreach ($img in $images) {
    Write-Host "   Pulling $img ..." -ForegroundColor DarkGray
    $ok = $false
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        docker pull $img
        if ($LASTEXITCODE -eq 0) { $ok = $true; break }
        Write-Host "   Attempt $attempt for $img failed (network hiccup). Retrying in 10s..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }
    if (-not $ok) { $failed += $img }
}
if ($failed.Count -gt 0) {
    Write-Host "`nERROR: could not download these images after 5 attempts each:" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
    Write-Host "This is a network/connectivity issue (e.g. an unstable connection), not a bug in the app." -ForegroundColor Red
    Write-Host "Simply run this script again later - images already downloaded are cached and won't restart." -ForegroundColor Red
    exit 1
}
Write-Host "All images downloaded successfully." -ForegroundColor Green

Write-Host "[1/6] Starting database only..." -ForegroundColor Green
docker compose up -d db

Write-Host "[2/6] Waiting for the database AND its app databases to be ready..." -ForegroundColor Green
# The image creates the my_geonode / my_geonode_data databases on first boot via
# an init script. We must wait for THOSE to exist, not just for the server to
# accept connections, otherwise the restore runs too early and fails.
do {
    Start-Sleep -Seconds 4
    $ready = docker exec db4my_geonode psql -U postgres -tAc "SELECT count(*) FROM pg_database WHERE datname IN ('my_geonode','my_geonode_data');" 2>$null
} until ("$ready".Trim() -eq "2")

Write-Host "[3/6] Restoring databases and granting app-user rights..." -ForegroundColor Green
docker cp data/my_geonode.sql       db4my_geonode:/tmp/my_geonode.sql
docker cp data/my_geonode_data.sql  db4my_geonode:/tmp/my_geonode_data.sql
# Restore as the postgres superuser (needed for the PostGIS extension objects)...
docker exec db4my_geonode psql -U postgres -d my_geonode      -f /tmp/my_geonode.sql      | Out-Null
docker exec db4my_geonode psql -U postgres -d my_geonode_data -f /tmp/my_geonode_data.sql | Out-Null
# ...then hand ownership/rights to the app users the app logs in as. Without this,
# the app gets "permission denied" on its own tables and fails to start.
$grant = "GRANT ALL ON SCHEMA public TO {0}; GRANT ALL ON ALL TABLES IN SCHEMA public TO {0}; GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO {0}; GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO {0}; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {0};"
docker exec db4my_geonode psql -U postgres -d my_geonode      -c ($grant -f "my_geonode")      | Out-Null
docker exec db4my_geonode psql -U postgres -d my_geonode_data -c ($grant -f "my_geonode_data") | Out-Null
Write-Host "   databases restored and permissions granted." -ForegroundColor DarkGray

Write-Host "[4/6] Restoring GeoServer config + media into volumes..." -ForegroundColor Green
$bundle = (Resolve-Path "data").Path -replace '\\','/'
docker run --rm -v my_geonode-gsdatadir:/gs -v "${bundle}:/bundle" alpine sh -c "cd /gs && tar xzf /bundle/geoserver_data.tar.gz"
docker run --rm -v my_geonode-media:/media  -v "${bundle}:/bundle" alpine sh -c "cd /media && tar xzf /bundle/media.tar.gz"

Write-Host "[5/6] Starting the backend (this pulls images the first time)..." -ForegroundColor Green
# Bring up django FIRST and wait for it to become healthy. GeoNode's first
# boot takes several minutes; starting everything at once can make dependent
# services give up. We wait here patiently instead.
docker compose up -d db rabbitmq memcached django

Write-Host "Waiting for the backend to finish its first-time setup (this can take 3-8 minutes)..." -ForegroundColor Green
$dready = $false
for ($i = 0; $i -lt 60; $i++) {
    $h = (docker inspect --format '{{.State.Health.Status}}' django4my_geonode 2>$null)
    if ($h -eq 'healthy') { $dready = $true; break }
    Start-Sleep -Seconds 15
    Write-Host "   ...backend still starting ($([int](($i+1)*15))s, status: $h)" -ForegroundColor DarkGray
}
if (-not $dready) {
    Write-Host "Backend is still not healthy. Showing the last log lines to help diagnose:" -ForegroundColor Yellow
    docker logs django4my_geonode --tail 25
    Write-Host "You can wait a bit longer and re-run 'docker compose up -d', or share these logs." -ForegroundColor Yellow
}

Write-Host "[6/6] Starting the remaining services (GeoServer, web app)..." -ForegroundColor Green
docker compose up -d
Start-Sleep -Seconds 5
docker compose restart geoserver | Out-Null

# The web app is a React dev server; it must COMPILE before it will respond.
# Wait for it so we don't tell the user it's ready before it actually is.
Write-Host "`nWaiting for the web app to finish compiling (can take a few minutes)..." -ForegroundColor Green
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
    Start-Sleep -Seconds 10
    Write-Host "   ...still compiling ($([int](($i+1)*10))s)" -ForegroundColor DarkGray
}

Write-Host ""
if ($ready) {
    Write-Host "======================================================" -ForegroundColor Cyan
    Write-Host "  READY. Open the application in your browser:" -ForegroundColor Cyan
    Write-Host "     ->  http://localhost:3000        <-- THE APP" -ForegroundColor Green
    Write-Host "======================================================" -ForegroundColor Cyan
} else {
    Write-Host "The web app is taking longer than usual to compile." -ForegroundColor Yellow
    Write-Host "Wait 1-2 more minutes, then open http://localhost:3000" -ForegroundColor Yellow
    Write-Host "(If it still won't load, try http://127.0.0.1:3000 instead.)" -ForegroundColor Yellow
}
Write-Host "`nOther services (optional):" -ForegroundColor DarkGray
Write-Host "   GeoNode admin portal :  http://localhost:3500" -ForegroundColor DarkGray
Write-Host "   GeoServer            :  http://localhost:8080/geoserver" -ForegroundColor DarkGray
