---
title: Sak Tmor API
emoji: 🗺️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
pinned: false
---

# Sak Tmor API

FastAPI backend for the Sak Tmor AI trip planner (TF-IDF recommendation + GA route optimization).

Runs as a Docker Space on port 8000.

## Endpoints
- `GET /api/provinces` — list provinces
- `POST /api/generate-trip` — generate itinerary

## Config
- `FRONTEND_ORIGIN` (env) — comma-separated allowed CORS origins (your Vercel URL).
