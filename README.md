# Pune Cooler Routes 🌿

**A shade-aware pedestrian navigation system for Pune, India.**

Walk cooler, smarter, and safer through Kothrud, Karve Road, Deccan Gymkhana, and FC Road by choosing routes that maximize tree and building shade — validated across an intensive 11-day research and development sprint.

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

## 11-Day Sprint Summary

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
| 10 | Dynamic sun-marching solar routing & walkability | `day10_walkability_audit.png`, `day10_walkability_corridors.csv`, `day10_safe_cool_benchmark.csv` |
| 11 | Physiological heat strain & Virtual Walker HUD | `day11_thermal_strain.png`, `day11_heat_strain_profiles.csv`, interactive simulation HUD |

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
│   ├── day5_server.py            # Days 5-11: Full-stack HTTP REST & static server
│   ├── day5_offline_map.py       # Day 5: Standalone Folium map
│   ├── day5_test.py              # Day 5: Automated API test suite
│   ├── day6_router.py            # Day 6: Multi-criteria thermal comfort routing
│   ├── day6_benchmark.py         # Day 6: 25-route benchmark suite
│   ├── day7_analytics.py         # Day 7: Network-wide shade analytics
│   ├── day7_ndvi_trees.py        # Day 7: OSM tree canopy integration
│   ├── day8_shade_heatmap.py     # Day 8: Network shade heatmap & composite score
│   ├── day8_isochrone.py         # Day 8: Standard vs Shade-priority isochrones
│   ├── day9_smart_planner.py     # Day 9: Heuristic intermediate waypoint planner
│   ├── day9_report_generator.py  # Day 9: Master self-contained HTML report builder
│   ├── day10_dynamic_router.py   # Day 10: Dynamic time-marching solar router
│   ├── day10_walkability.py      # Day 10: Walkability safety audit & benchmark
│   └── day11_heat_strain.py      # Day 11: Biometeorological heat strain & hydration
├── web/
│   ├── index.html                # Complete UI (Virtual Walker HUD, Heat Strain, Stepper, Overlays)
│   ├── style.css                 # Midnight Glassmorphism theme with micro-animations
│   └── app.js                   # Leaflet map logic, animated walker, real-time gauges
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
│   ├── day9_report.md
│   ├── day10_report.md
│   ├── day11_report.md
│   ├── day9_full_report.html     # Self-contained master report
│   ├── day10_walkability_audit.png
│   ├── day10_walkability_corridors.csv
│   ├── day10_safe_cool_benchmark.csv
│   ├── day11_thermal_strain.png
│   └── day11_heat_strain_profiles.csv
└── requirements.txt
```

---

## Key Results Across Sprints

### 1. Dynamic Sun-Marching & Solar Heat Shielding (Day 10)
- Traditional routing assumes a static noon angle. Day 10 continuously advances the solar trajectory as pedestrians walk.
- In peak 13:00 sun across 10 benchmark routes:
  - Average shade increase: **+9.3%**
  - Average detour: only **+224.8 metres (+1.2 min)**
  - Direct solar heat radiation avoided: **123.0 kJ** on typical university commutes

### 2. Corridor Walkability & Safety Rankings (Day 10)
1. **Senapati Bapat Marg** — 87.6 Walkability Score (95% sidewalk continuity, 100% shade coverage)
2. **Bhandarkar Road** — 50.0 Walkability Score (Dense banyan tree canopy)
3. **Karve Road** — 24.5 Walkability Score (Arterial corridor, high tree canopy buffer)
4. **Prabhat Road** — 24.5 Walkability Score (Quiet residential tree canopy)

### 3. Biometeorological Heat Strain Relief (Day 11)
- Pedestrian sweat loss rate in unshaded sun: **up to 345 mL/hour**.
- Shaded Dynamic Safe+Cool route reduces sweat rate by **15 to 25 mL/hour**, saving over **65 mL of fluid per commute**.
- Automated canopy rest stop algorithm flags shaded pause nodes every 15–25 minutes.

### 4. Interactive Virtual Walker HUD (Day 11)
- Real-time animated pedestrian avatar moves along the polyline with variable simulation playback speeds (1x, 5x, 15x).
- Live dashboard displaying instantaneous shade percentage, solar flux ($W/m^2$), and elapsed transit time.

---

## Run Individual Scripts

```bash
# Day 10 scripts
python scripts/day10_dynamic_router.py  # Test dynamic sun-marching route solver
python scripts/day10_walkability.py     # Run 10-corridor walkability audit & benchmark

# Day 11 scripts
python scripts/day11_heat_strain.py     # Run physiological heat strain & hydration models

# Launch interactive web server
python scripts/day5_server.py 8050      # Serves web UI, REST API, & GeoJSON layers
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
| Shadow Simulation | pybdshadow (09:00, 13:00, 16:00, May 15, 2024) + OSM Green Canopy |

---

*Built during an 11-day research and development sprint | Data: OpenStreetMap contributors*
