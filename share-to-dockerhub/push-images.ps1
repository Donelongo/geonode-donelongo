# =============================================================================
#  push-images.ps1  -  Push the 6 images to your Docker Hub (donelongo/...).
#  FIRST run:   docker login -u donelongo      (enter your Docker Hub password)
#  Then:        .\share-to-dockerhub\push-images.ps1
# =============================================================================
$HubUser = "donelongo"

$images = @(
    "geonode-app:4.4.2",
    "geonode-frontend:latest",
    "geonode-nginx:1.25.3-latest",
    "geonode-geoserver:2.24.4-v1",
    "geonode-geoserver-data:2.24.4-v1",
    "geonode-postgis:15.3-latest"
)

foreach ($img in $images) {
    Write-Host "`n==== Pushing $HubUser/$img ====" -ForegroundColor Green
    docker push "$HubUser/$img"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nPush FAILED for $HubUser/$img (exit $LASTEXITCODE)." -ForegroundColor Red
        Write-Host "If it says 'unauthorized', run:  docker login -u $HubUser   then re-run this script." -ForegroundColor Red
        exit 1
    }
}

Write-Host "`nAll images pushed: https://hub.docker.com/u/$HubUser" -ForegroundColor Cyan
Write-Host "Now zip 'share-to-dockerhub\boss-bundle' and send it to your boss." -ForegroundColor Yellow
