# 🌿 Pune Cooler Routes — Shade-Aware Pedestrian Navigation System

A comprehensive, physics-informed walking navigation application for **Pune, Maharashtra, India**. The system dynamically routes pedestrians along tree canopies and building shadows to minimize extreme urban heat exposure while balancing walking time and sidewalk safety.

---

## 🗺️ Pilot Corridor
* **City**: Pune, Maharashtra, India
* **Bounding Box (WGS84)**: `west 73.802, south 18.495, east 73.846, north 18.531` (~4.6 km × 4.0 km)
* **Neighborhoods**: Kothrud, Karve Road, Deccan Gymkhana, Fergusson College Road, Prabhat Road, BMCC, Law College Road.
* **Walking Network**: 3,971 intersection nodes, 10,414 edges (638.4 km total network length).

---

## 🚀 6-Day Development Journey & Architecture

```
                 [OpenStreetMap Topologies]
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   [Pedestrian Network]             [Buildings & Tree Canopies]
   (OSMnx 2.1.1, 10k edges)         (Polygons + Canopies, 6-10m)
            │                                 │
            │                        [Solar Simulation]
            │                        (pybdshadow Sun Path)
            │                                 │
            └───────────────┬─────────────────┘
                            ▼
                [Dynamic Shaded Graph]
            (09:00 Morning, 13:00 Midday, 16:00 Afternoon)
                            │
            ┌───────────────┴────────────────┐
            ▼                                ▼
  [Fastest Route Engine]           [Multi-Criteria Thermal Engine]
  (Dijkstra on physical length)    (Shade + Sidewalk Quality + Safety)
            │                                │
            └───────────────┬────────────────┘
                            ▼
          [Interactive Web App & Visualizer]
     (Leaflet.js • Dark Matter • Rest API • HUD Metrics)
```

### Day-by-Day Progression
* **Day 1 — Network Base & Sidewalk Audit**: Downloaded pilot walking network using OSMnx, snapped test route (MIT-WPU to Fergusson College: 4,339m), and conducted sidewalk tagging audit across 10,414 edges.
* **Day 2 — Building Footprints & Heights**: Extracted building geometries with level/height parsing and 6.0m fallbacks (`buildings.gpkg`).
* **Day 3 — Solar Shadow Modeling**: Simulated solar azimuth and elevation (`pybdshadow`) for 09:00, 13:00, and 16:00, integrating tree canopies and covered arcades.
* **Day 4 — Dual-Route Routing Engine**: Implemented dual-path Dijkstra engine comparing raw length against shade-inflated `cool_weight`.
* **Day 5 — Interactive Web App & REST API**: Built fullstack Leaflet web app (`web/`), local server (`scripts/day5_server.py`), landmark presets, live sun angle toggles, and offline standalone map (`outputs/day5_map.html`).
* **Day 6 — Multi-Criteria Thermal Routing & Benchmark Suite**: Integrated sidewalk quality penalties, modeled continuous solar radiation exposure (W/m²), dynamic time-marching walk progress, and executed a 25-route benchmark suite (`outputs/day6_benchmark.png`).

---

## 📊 Day 6 Benchmark Results (25 Pune Pilot Routes)

Evaluated across 25 origin-destination pairs at peak mid-summer sun angle (13:00):

| Metric | Fastest Route | Coolest Route | Delta / Improvement |
|---|---|---|---|
| **Average Shade Exposure** | 30.2% | **34.4%** | **+4.2%** shade gain (up to **+25.3%** on shaded avenues) |
| **Average Walking Distance** | 2,382.8 m | 2,427.4 m | **+44.6 m** (only +1.8% detour!) |
| **Average Walking Duration** | 29.8 min | 30.3 min | **+0.6 min** extra walking |
| **Absorbed Solar Irradiance** | 728.0 W/m² | **693.2 W/m²** | **-34.8 W/m²** solar radiation avoided |
| **Apparent Radiant Relief** | Baseline | Substantial cooling | **-3.2°C** cooler thermal sensation |

> **Key Finding**: Pune pedestrians can gain significant heat relief and shade coverage with an average walking detour of **less than 45 metres (+36 seconds)**.

---

## 💻 How to Run

### 1. Launch the Interactive Web Application
```bash
# Start the local server (port 8050)
python scripts/day5_server.py 8050

# Open in your browser:
# http://127.0.0.1:8050
```
* **Features in the UI**:
  * Drop custom pins anywhere on the map or select from 9 Pune landmark presets.
  * Adjust sun position: Morning (09:00), Midday (13:00), Afternoon (16:00), or Live Computer Clock.
  * Fine-tune the Coolness Priority Slider (1.0x to 5.0x shade penalty).
  * View side-by-side metric cards (Distance, Duration, Shade %, Delta Advantage).
  * Step-by-step turn guidance with shade indicators.
  * Export calculated route GeoJSON for GPS/mobile use.

### 2. Run the Benchmark Suite & Generate Visuals
```bash
python scripts/day6_benchmark.py
# Outputs: outputs/day6_benchmark.png, outputs/day6_benchmark_25routes.csv, outputs/day6_report.md
```

### 3. Generate Standalone Offline Map
```bash
python scripts/day5_offline_map.py
# Outputs: outputs/day5_map.html
```

---

## 📁 Repository Structure
```
pune-cooler-routes/
├── data/
│   └── processed/
│       ├── network.graphml        # 3,971-node walking graph
│       ├── edges_shaded.gpkg       # 10,414 edges with 09:00/13:00/16:00 shade fracs
│       └── buildings.gpkg          # Building geometries
├── scripts/
│   ├── config.py                  # Coordinate bounding boxes & constants
│   ├── day4_router.py             # Base dual-route engine
│   ├── day5_engine.py             # Arbitrary-coordinate routing engine
│   ├── day5_server.py             # REST API & static asset server
│   ├── day5_offline_map.py        # Standalone Folium map generator
│   ├── day5_test.py               # Day 5 automated test suite
│   ├── day6_router.py             # Multi-criteria thermal comfort engine
│   ├── day6_benchmark.py          # 25-route benchmark & plot generator
│   └── enrich_network_shade.py    # Canopy & building shade enrichment
├── web/
│   ├── index.html                 # Responsive web layout
│   ├── style.css                  # Midnight glassmorphic design system
│   └── app.js                     # Leaflet routing & UI controller
└── outputs/
    ├── day6_benchmark.png         # Multi-panel benchmark visualization figure
    ├── day6_benchmark_25routes.csv# Full 25-route tabular metrics
    ├── day6_report.md             # Comprehensive final report
    ├── day5_report.md             # Day 5 verification report
    ├── day5_map.html              # Standalone interactive browser map
    └── routes_day5.geojson        # Dual-route GeoJSON export
```

---

## 🎓 Academic & Open-Source Credits
* **City Topologies**: [OpenStreetMap](https://www.openstreetmap.org/) contributors
* **Network Analysis**: [OSMnx](https://osmnx.readthedocs.io/) (Boeing, 2017)
* **Shadow Simulation**: [pybdshadow](https://pybdshadow.readthedocs.io/)
* **Cartography**: [Leaflet.js](https://leafletjs.com/) with CartoDB Dark Matter tiles
