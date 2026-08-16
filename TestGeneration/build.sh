#!/usr/bin/env bash
set -euo pipefail

echo "=== Step 1: Installing Python dependencies ==="
pip install -r requirements.txt pyinstaller

echo "=== Step 2: Bundling Python backend with PyInstaller ==="
pyinstaller \
  --onefile \
  --name app \
  --add-data "backend/agents/skills:backend/agents/skills" \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols \
  --hidden-import uvicorn.protocols.http \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.websockets \
  --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import uvicorn.lifespan \
  --hidden-import uvicorn.lifespan.on \
  --collect-all playwright \
  backend/app_entry.py

echo "=== Step 3: Building Vite frontend ==="
cd frontend
npm run build
cd ..

echo "=== Step 4: Packaging with electron-builder ==="
npm run dist

echo "=== Build complete ==="
