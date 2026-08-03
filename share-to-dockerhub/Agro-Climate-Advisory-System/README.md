# Agro-Climate Advisory & Wheat Land-Suitability System

A geospatial decision-support application for wheat land-suitability mapping and
agro-climate advisories. This package lets you run the complete system locally
with Docker for evaluation — no source code or developer setup required. All
application images are pulled automatically from Docker Hub.

## Requirements
- **Docker Desktop** (Windows/Mac) or **Docker Engine + Compose** (Linux), running.
- **At least 8 GB of RAM allocated to Docker** (in Docker Desktop: Settings → Resources).
  The stack runs several services; with less it may crash during startup. 10 GB free disk.
- Ports free on your machine: **3500** (GeoNode), **3000** (web app), **8080** (GeoServer).

> **First start takes time.** The backend (GeoNode) does a one-time setup that can
> take **3–8 minutes** before it reports healthy — this is normal. The start script
> waits for it and shows progress; please let it finish rather than stopping it.

## Run it (one command)
Open a terminal **inside this folder** and run:

- **Windows (PowerShell):**
  ```powershell
  .\start.ps1
  ```
- **Linux / macOS:**
  ```bash
  chmod +x start.sh && ./start.sh
  ```

The first run downloads the images (a few GB) and restores the data, so allow
10–15 minutes. **The script waits for the app to finish compiling and then prints
`READY` with the URL — don't open the app until you see that.**

## Open the app

### 👉 The application is at **http://localhost:3000**
That is the main app to review (map, land-suitability, advisories, disease info).

> **Important:** the app needs 1–2 minutes to compile the first time. If
> `http://localhost:3000` says "can't connect," it simply isn't ready yet —
> wait for the `READY` message from the start script, then refresh. If `localhost`
> still won't load, try **http://127.0.0.1:3000** (same app, forces IPv4).

Other services, only if you want them:

| Service | URL |
|---------|-----|
| GeoNode admin portal (`/admin`) | http://localhost:3500 |
| GeoServer | http://localhost:8080/geoserver |

## Stop / start again
```bash
docker compose stop      # stop, keep data
docker compose start     # start again
docker compose down      # stop and remove containers (data volumes are kept)
```

## Notes
- The data (wheat clusters, suitability layers, advisories, disease info, uploaded
  images) is restored from the `data/` folder on first startup.
- If a page looks empty right after launch, wait a minute and refresh — GeoServer
  and Django are still warming up.
