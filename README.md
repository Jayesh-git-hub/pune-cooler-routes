# Pune Cooler Routes 🌿

**A shade-aware pedestrian navigation system for Pune, India.**

Walk cooler, smarter, and safer through Kothrud, Karve Road, Deccan Gymkhana, and FC Road by choosing routes that maximize tree and building shade — validated across an intensive 9-day research and development sprint.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the interactive web app
python scripts/day5_server.py 8050
# Open http://127.0.0.1:8050 in your browser
```

---

## 9-Day Sprint Summary

| Day | Focus Area | Key Output |
|---|---|---|
| 1 | Network download + sidewalk audit | `network.graphml`, `sidewalk_audit.png` |
| 2 | Building heights from OSM | `buildings_with_heights.gpkg` |
| 3 | Shadow simulation (pybdshadow) | `edges_shaded.gpkg` (3 time slots) |
| 4 | Dual routing engine | `routes_day4.geojson`, `day4_report.md` |
| 5 | Full-stack web app + REST API | `day5_map.html`, `routes_day5.geojson` |
| 6 | Multi-criteria thermal routing + benchmark | `day6_benchmark.png`, `day6_benchmark_25routes.csv` |
| 7 | Network analytics + tree canopy integration | `day7_analytics.png`, `day7_shade_tiers.csv`, `day7_canopy_map.png` |
| 8 | Shade heatmap + isochrone reachability | `day8_shade_heatmap.png`, `day8_isochrone_comparison.png`, `day8_heatmap.geojson` |
| 9 | Smart waypoint planner + full executive report | `day9_smart_planner.png`, `day9_full_report.html`, URL sharing |

---

## Project Architecture

```
pune-cooler-routes/
├── scripts/
│   ├── config.py                 # Shared paths and constants
│   ├── download_network.py       # Day 1: OSMnx walking network
│   ├── sidewalk_audit.py         # Day 1: Sidewalk quality audit
│   ├── download_buildings_osm.py # Day 2: Building footprints + heights
│   ├── process_buildings.py      # Day 2: Height enrichment
│   ├── day3_shadows.py           # Day 3: pybdshadow solar shadow simulation
│   ├── enrich_network_shade.py   # Day 3: Shade fraction assignment to edges
│   ├── day4_router.py            # Day 4: Dual routing (Fastest + Coolest)
│   ├── day5_engine.py            # Day 5: Extended routing engine
│   ├── day5_server.py            # Day 5-9: HTTP REST server + static & GeoJSON serving
│   ├── day5_offline_map.py       # Day 5: Standalone Folium map
│   ├── day5_test.py              # Day 5: Automated API test suite
│   ├── day6_router.py            # Day 6: Multi-criteria thermal comfort routing
│   ├── day6_benchmark.py         # Day 6: 25-route benchmark suite
│   ├── day7_analytics.py         # Day 7: Network-wide shade analytics
│   ├── day7_ndvi_trees.py        # Day 7: OSM tree canopy integration
│   ├── day8_shade_heatmap.py     # Day 8: Network shade heatmap & composite score
│   ├── day8_isochrone.py         # Day 8: Standard vs Shade-priority isochrones
│   ├── day9_smart_planner.py     # Day 9: Heuristic intermediate waypoint planner
│   └── day9_report_generator.py  # Day 9: Master self-contained HTML report builder
├── web/
│   ├── index.html                # Day 9 UI (3 routes, heatmap overlay, isochrones, history, URL share)
│   ├── style.css                 # Dark glassmorphism theme & micro-animations
│   └── app.js                   # Leaflet map logic, live overlays, deep linking
├── data/
│   ├── processed/
│   │   ├── network.graphml       # Walking graph (3,971 nodes, 10,414 edges)
│   │   ├── edges_shaded.gpkg     # Shade fracs + tree_shade_bonus per edge
│   │   └── buildings_with_heights.gpkg
│   └── raw/
├── outputs/
│   ├── day1_report.md
│   ├── day2_report.md
│   ├── day3_report.md
│   ├── day4_report.md
│   ├── day5_report.md
│   ├── day6_report.md
│   ├── day7_report.md
│   ├── day8_report.md
│   ├── day8_isochrone_report.md
│   ├── day9_report.md
│   ├── day9_smart_planner_report.md
│   ├── day9_full_report.html     # Self-contained 9-day master report (all figures embedded)
│   ├── day8_heatmap.geojson      # Interactive heatmap overlay
│   ├── day8_isochrone_shaded.geojson
│   ├── day8_isochrone_standard.geojson
│   ├── day8_neighbourhood_scores.csv
│   └── day9_waypoint_recommendations.csv
└── requirements.txt
```

---

## Key Results

### 1. Routing Benchmark (Day 6 — 25 Origin-Destination Pairs)

| Metric | Fastest Route | Coolest Route | Delta |
|---|---|---|---|
| Avg Shade | 30.2% | 34.4% | **+4.2%** |
| Avg Distance | 2,382.8 m | 2,427.4 m | +44.6 m |
| Avg Duration | 29.8 min | 30.3 min | +0.6 min |
| Solar Irradiance | 728.0 W/m² | 693.2 W/m² | **−34.8 W/m²** |
| Apparent Temp Relief | — | — | **−3.2°C** |

> Walk **+44.6 metres more** to gain **4.2% more shade** and feel **3.2°C cooler**!

### 2. Isochrone Reachability (Day 8 — 10-Minute Walk from Deccan Gymkhana)
- Standard walk reachable edges: **57.5%** well-shaded
- Shade-priority walk reachable edges: **69.4%** well-shaded (**+11.9% improvement**)

### 3. Neighbourhood Shade Rankings (Day 8)
1. **Law College Rd** — 40.6% composite shade (7.2% tree bonus)
2. **Senapati Bapat Marg** — 39.8% composite shade (6.5% tree bonus)
3. **FC Road / Deccan** — 37.3% composite shade (3.5% tree bonus)
4. **Prabhat Rd / JM Rd** — 36.1% composite shade (2.9% tree bonus)
5. **Karve Road** — 35.8% composite shade (1.5% tree bonus)
6. **Kothrud Core** — 33.9% composite shade (1.3% tree bonus)

### 4. Smart Waypoint Planner (Day 9)
For long commutes (e.g. MIT-WPU to Fergusson College), routing via intermediate corridors like **Senapati Bapat Marg** or **Chhatrapati Sambhaji Garden** allows pedestrians to bypass high-irradiance segments while keeping detour times under acceptable walking bounds.

---

## Run Individual Scripts

```bash
# Day 8 scripts
python scripts/day8_shade_heatmap.py    # Compute composite shade & export heatmap GeoJSON
python scripts/day8_isochrone.py        # Compute 5/10/15-min standard & shade isochrones

# Day 9 scripts
python scripts/day9_smart_planner.py    # Rank best intermediate shady waypoints
python scripts/day9_report_generator.py # Compile outputs/day9_full_report.html

# Launch interactive web server
python scripts/day5_server.py 8050      # Serve web UI, REST API, & GeoJSON layers
```

---

## Pilot Area

| Parameter | Value |
|---|---|
| City | Pune, Maharashtra, India |
| Pilot Bbox | 73.802°E – 73.846°E, 18.495°N – 18.531°N |
| Focus Roads | Karve Road, Senapati Bapat Marg, FC Road, Law College Road |
| Nodes | 3,971 |
| Edges | 10,414 |
| Shadow Simulation | pybdshadow (09:00, 13:00, 16:00, May 15, 2024) |

---

## Tech Stack

- **Python 3.11+** — Core language
- **OSMnx 2.x** — OpenStreetMap network download + routing
- **NetworkX** — Dijkstra shortest-path algorithm
- **GeoPandas + Shapely** — Geospatial data processing
- **pybdshadow** — Building shadow casting simulation
- **Matplotlib** — Analytics and publication figures
- **Leaflet.js** — Interactive map frontend
- **Vanilla CSS** — Dark glassmorphism theme (no frameworks)
- **Python http.server** — Lightweight REST API + GeoJSON/HTML server

---

*Built during a 9-day research and development sprint | Data: OpenStreetMap contributors*
