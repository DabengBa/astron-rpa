# Offline portable build pipeline (Windows)

This repo ships a fully-offline “stand-alone portable” build as a single zip.

## One-command build

From repo root:

- `build.bat -p "C:\Program Files\Python313\python.exe" -s "C:\Program Files\7-Zip\7z.exe"`

Options:
- `--skip-engine` build Electron only
- `--skip-frontend` build engine runtime only

## What the build produces

### Engine runtime
`build.bat` generates:

- `resources/python_core.7z`
- `resources/python_core.7z.sha256.txt`

These are consumed by Electron main process on first launch:

- It scans `resources/*.7z`
- Extracts into portable work dir `./data/runtime/...`
- Uses `*.sha256.txt` to decide whether re-extract is needed

### Electron desktop app
The frontend build outputs:

- `frontend/packages/electron-app/dist/` (electron-builder output)

## Final zip assembly

MVP assembly (manual):

1. Create an empty folder `AstronRPA/`
2. Copy Electron packaged output into `AstronRPA/`
3. Ensure `AstronRPA/resources/` contains `python_core.7z` and its `.sha256.txt`
4. Zip `AstronRPA/`

Portable runtime data will be created on first start inside:

- `AstronRPA/data/` (work dir)
- `AstronRPA/config/` (runtime config)

## Offline constraints

- Default profile is OFFLINE: no auto-update check, no network egress.
- All services should be loopback-only.
