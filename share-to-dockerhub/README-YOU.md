# How to share the app with your boss (your steps)

Everything here is already prepared. You only run three things.

## 0. The `.env` file — ALREADY DONE
`boss-bundle/.env` has already been created for you, with your **email address and
email password removed** so your boss never sees them. Nothing to do here.
(Email/subscribe sending is disabled in the bundle; everything else works.)

## 1. Build the images (bakes your CURRENT code in)
From the project root:
```powershell
.\share-to-dockerhub\build-images.ps1
```
The frontend image runs a full `npm run`/`npm install`, so this takes ~10-15 min.

## 2. Log in and push to Docker Hub
```powershell
docker login -u donelongo          # enter your Docker Hub password
.\share-to-dockerhub\push-images.ps1
```
Total upload is a few GB — depends on your connection. Repos appear at
https://hub.docker.com/u/donelongo

## 3. Send the bundle to your boss
Zip the `share-to-dockerhub\boss-bundle` folder (make sure `.env` is inside it from
step 0) and send it to him — email, Google Drive, WeTransfer, anything.

Your boss then just unzips it and runs `start.ps1` (Windows) or `start.sh`
(Linux/Mac). Docker pulls your images from Docker Hub and the data restores
automatically. Full instructions for him are in `boss-bundle/README.md`.

---
### What your boss actually does
1. Install Docker Desktop, make sure it's running.
2. Unzip the folder you sent.
3. Run `start.ps1` / `start.sh`.
4. Open http://localhost:3000 (web app) and http://localhost:3500 (GeoNode).

That's the closest thing to "pull it and it just works" for a multi-service app:
one command that pulls every image and boots the whole thing with your data inside.
