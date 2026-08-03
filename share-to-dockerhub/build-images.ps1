# =============================================================================
#  build-images.ps1  -  Build the images your boss will pull from Docker Hub.
#  Run this from the geonode project root:  .\share-to-dockerhub\build-images.ps1
#
#  It bakes your CURRENT code into two images (app + frontend) and re-tags the
#  four config images that are already built locally. No data is baked in here -
#  the data ships as a small bundle that restore-data restores on the boss's side.
# =============================================================================
$ErrorActionPreference = "Stop"
$HubUser = "donelongo"

# Resolve the project root (parent of this script's folder)
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Write-Host "Project root: $root" -ForegroundColor Cyan

Write-Host "`n[1/6] Building app image (current backend code)..." -ForegroundColor Green
docker build -f share-to-dockerhub/Dockerfile.app -t "$HubUser/geonode-app:4.4.2" .

Write-Host "`n[2/6] Building frontend image (current React source)..." -ForegroundColor Green
# Context is the frontend folder so its .dockerignore excludes the 1 GB node_modules.
docker build -f share-to-dockerhub/Dockerfile.frontend -t "$HubUser/geonode-frontend:latest" agro-climate-advisory-system-frontend

# The remaining images hold only config (no stale app code), so we just re-tag
# the ones your local stack already built.
Write-Host "`n[3/6] Tagging nginx..." -ForegroundColor Green
docker tag my_geonode/nginx:1.25.3-latest        "$HubUser/geonode-nginx:1.25.3-latest"
Write-Host "[4/6] Tagging geoserver..." -ForegroundColor Green
docker tag my_geonode/geoserver:2.24.4-v1        "$HubUser/geonode-geoserver:2.24.4-v1"
Write-Host "[5/6] Tagging geoserver_data..." -ForegroundColor Green
docker tag my_geonode/geoserver_data:2.24.4-v1   "$HubUser/geonode-geoserver-data:2.24.4-v1"
Write-Host "[6/6] Tagging postgis..." -ForegroundColor Green
docker tag my_geonode/postgis:15.3-latest        "$HubUser/geonode-postgis:15.3-latest"

Write-Host "`nDone. Images ready:" -ForegroundColor Cyan
docker images --format "  {{.Repository}}:{{.Tag}}  {{.Size}}" | Select-String "$HubUser/geonode-"
Write-Host "`nNext:  docker login -u $HubUser   then   .\share-to-dockerhub\push-images.ps1" -ForegroundColor Yellow
