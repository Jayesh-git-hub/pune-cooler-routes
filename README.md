# Pune Cooler Routes 🌿

**A shade-aware pedestrian navigation system for Pune, India.**

Walk cooler, smarter, and safer through Kothrud, Karve Road, Deccan Gymkhana, and FC Road by choosing routes that maximize tree and building shade — validated by a 7-day intensive research sprint.

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

## 7-Day Sprint Summary

| Day | Focus Area | Key Output |
|---|---|---|
| 1 | Network download + sidewalk audit | `network.graphml`, `sidewalk_audit.png` |
| 2 | Building heights from OSM | `buildings_with_heights.gpkg` |
| 3 | Shadow simulation (pybdshadow) | `edges_shaded.gpkg` (3 time slots) |
| 4 | Dual routing engine | `routes_day4.geojson`, `day4_report.md` |
| 5 | Full-stack web app + REST API | `day5_map.html`, `routes_day5.geojson` |
| 6 | Multi-criteria thermal routing + benchmark | `day6_benchmark.png`, `day6_benchmark_25routes.csv` |
| 7 | Network analytics + tree canopy integration | `day7_analytics.png`, `day7_shade_tiers.csv`, `day7_canopy_map.png` |

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
│   ├── day5_server.py            # Day 5-7: HTTP REST server + web serving
│   ├── day5_offline_map.py       # Day 5: Standalone Folium map
│   ├── day5_test.py              # Day 5: Automated API test suite
│   ├── day6_router.py            # Day 6: Multi-criteria thermal comfort routing
│   ├── day6_benchmark.py         # Day 6: 25-route benchmark suite
│   ├── day7_analytics.py         # Day 7: Network-wide shade analytics
│   └── day7_ndvi_trees.py        # Day 7: OSM tree canopy integration
├── web/
│   ├── index.html                # Day 7 upgraded UI (3-route, thermal, mode toggle)
│   ├── style.css                 # Dark glassmorphism theme
│   └── app.js                   # Interactive Leaflet map logic
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
│   ├── day5_map.html             # Standalone interactive map
│   ├── day6_report.md
│   ├── day6_benchmark.png
│   ├── day6_benchmark_25routes.csv
│   ├── day7_report.md            # Final comprehensive report
│   ├── day7_analytics.png        # 4-panel network shade analytics
│   ├── day7_shade_tiers.csv      # Per-edge shade tier classification
│   └── day7_canopy_map.png       # Road network coloured by tree canopy
└── requirements.txt
```

---

## Key Results

### Routing Benchmark (Day 6 — 25 Origin-Destination Pairs)

| Metric | Fastest Route | Coolest Route | Delta |
|---|---|---|---|
| Avg Shade | 30.2% | 34.4% | **+4.2%** |
| Avg Distance | 2,382.8 m | 2,427.4 m | +44.6 m |
| Avg Duration | 29.8 min | 30.3 min | +0.6 min |
| Solar Irradiance | 728.0 W/m² | 693.2 W/m² | **−34.8 W/m²** |
| Apparent Temp Relief | — | — | **−3.2°C** |

> Walk **+44.6 metres more** to gain **4.2% more shade** and feel **3.2°C cooler**!

### Network Shade Analytics (Day 7 — All 10,414 Edges)

| Shade Tier | Edges | Percentage |
|---|---|---|
| Deep Canopy (≥60%) | 100 | 1.0% |
| Moderate Shade (35–60%) | 332 | 3.2% |
| Partial Shade (15–35%) | 7,872 | 75.6% |
| Full Sun (<15%) | 2,110 | 20.3% |

### Top Shadiest Walking Corridors (Midday)
1. **Senapati Bapat Marg** — 56.1% shade (4,992 m corridor)
2. **Bhandarkar Path** — 56.1% shade (2,446 m)
3. **Admiral Somnath Path** — 56.2% shade (2,531 m)
4. **Vishnushastri Chiplunkar Path** — 57.4% shade (3,940 m)
5. **Sambhaji Bridge** — 57.4% shade (1,035 m)

---

## Run Individual Scripts

```bash
# Day 7 scripts
python scripts/day7_analytics.py      # Generate network analytics figure + CSV
python scripts/day7_ndvi_trees.py     # Download OSM tree canopy + update edges

# Day 6 scripts
python scripts/day6_benchmark.py      # Run 25-route benchmark
python scripts/day6_router.py         # Test multi-criteria routing

# Launch web server
python scripts/day5_server.py 8050    # Serve full web app at :8050
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
- **Matplotlib** — Analytics figures
- **Leaflet.js** — Interactive map frontend
- **Vanilla CSS** — Dark glassmorphism theme (no frameworks)
- **Python http.server** — Lightweight REST API + static file server

---

## Roadmap (v2.0)

1. Digital Elevation Model (DEM) for hill-aware shadow calculation
2. Land Surface Temperature (LST) satellite data for albedo corrections
3. Per-footpath shading on wide roads (not just centerline)
4. Covered walkway / awning detection from street-level imagery
5. Air quality and traffic weighting

---

*Built during a 7-day research sprint | Data: OpenStreetMap contributors*
