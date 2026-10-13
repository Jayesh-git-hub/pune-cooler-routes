# Pune Cooler Routes - Pilot (Kothrud to FC Road)

A shade-aware walking navigation application for Pune, India that dynamically computes both the **Fastest** and **Coolest** walking routes using OpenStreetMap networks, building geometries, tree canopy corridors, and solar shadow simulation (`pybdshadow`).

## Pilot Area (WGS84)
* **Bounding Box**: west 73.802, south 18.495, east 73.846, north 18.531 (Kothrud, Karve Road, Deccan Gymkhana, FC Road)
* **Walking Network**: 3,971 nodes, 10,414 edges (638.4 km total network)

## Day 5 Interactive Web Application
* **Interactive Web Map**: Fullstack browser UI powered by Leaflet.js with CartoDB Dark Matter styling.
* **REST API**: Built-in Python HTTP server serving dynamic routing at `/api/route`.
* **Dynamic Features**:
  * Pick any origin & destination by clicking directly on the map or choosing Pune landmark presets.
  * Real-time sun angle selection: 09:00 (Morning), 13:00 (Midday), 16:00 (Afternoon), or live wall-clock time.
  * Coolness priority slider (1.0x to 5.0x shade weighting).
  * Direct trade-off dashboard: Δ distance, Δ walking time, and Δ shade gain percentage.
  * Turn-by-turn walking steps with shade icons.
  * Export routes to GeoJSON for mobile navigation.

## Commands to Run
* **Launch Web App**:
  ```bash
  python scripts/day5_server.py 8050
  # Open http://127.0.0.1:8050
  ```
* **Run Automated Day 5 Test Suite**:
  ```bash
  python scripts/day5_test.py
  ```
* **Generate Standalone Browser Map**:
  ```bash
  python scripts/day5_offline_map.py
  # Generates outputs/day5_map.html
  ```
* **Run Base Dual-Route Engine**:
  ```bash
  python scripts/day4_router.py
  ```
