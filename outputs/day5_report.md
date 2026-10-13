# Pune Cooler Routes - Day 5 Report

## Executive Summary
Day 5 transforms our mathematical dual-routing engine into a fully interactive web application with:
1. **Interactive Fullstack Web App**: Leaflet map UI with dark theme, dynamic pin drops, landmark presets, sun-angle time controls, and coolness sliders.
2. **Local REST API**: Lightweight Python HTTP server (`scripts/day5_server.py`) with `/api/route`, `/api/landmarks`, and `/api/status`.
3. **Standalone Interactive Map**: Pre-rendered self-contained Folium map (`outputs/day5_map.html`).
4. **Export Capabilities**: Client-side & server-side GeoJSON generation for real-world navigation.

---

## Benchmark Results (5 Pune Landmark Routes Across 3 Sun Angles)

All numbers below were computed dynamically across our 3,971-node Pune pilot network:

| Route | Hour | Fastest Route | Fast Shade | Coolest Route | Cool Shade | Detour Penalty | Shade Gain |
|---|---|---|---|---|---|---|---|
| MIT-WPU Campus ➔ Fergusson College | 09:00 | 4339.0 m (54.2m) | 60.6% | 4415.0 m (55.2m) | 64.2% | +76.0 m (+1.0 min) | **+3.6%** |
| MIT-WPU Campus ➔ Fergusson College | 13:00 | 4339.0 m (54.2m) | 40.1% | 4421.5 m (55.3m) | 45.6% | +82.5 m (+1.1 min) | **+5.5%** |
| MIT-WPU Campus ➔ Fergusson College | 16:00 | 4339.0 m (54.2m) | 66.5% | 4429.1 m (55.4m) | 70.1% | +90.1 m (+1.2 min) | **+3.6%** |
| Deccan Gymkhana ➔ ILS Law College | 09:00 | 3545.1 m (44.3m) | 60.0% | 3551.6 m (44.4m) | 60.9% | +6.5 m (+0.1 min) | **+0.9%** |
| Deccan Gymkhana ➔ ILS Law College | 13:00 | 3545.1 m (44.3m) | 41.6% | 3545.1 m (44.3m) | 41.6% | +0.0 m (+0.0 min) | **+0.0%** |
| Deccan Gymkhana ➔ ILS Law College | 16:00 | 3545.1 m (44.3m) | 65.2% | 3545.1 m (44.3m) | 65.2% | +0.0 m (+0.0 min) | **+0.0%** |
| BMCC ➔ Sambhaji Garden | 09:00 | 1719.1 m (21.5m) | 57.8% | 1758.7 m (22.0m) | 61.1% | +39.6 m (+0.5 min) | **+3.3%** |
| BMCC ➔ Sambhaji Garden | 13:00 | 1719.1 m (21.5m) | 39.5% | 1726.7 m (21.6m) | 42.0% | +7.6 m (+0.1 min) | **+2.5%** |
| BMCC ➔ Sambhaji Garden | 16:00 | 1719.1 m (21.5m) | 61.6% | 1726.7 m (21.6m) | 63.2% | +7.6 m (+0.1 min) | **+1.6%** |
| Kamla Nehru Park ➔ FC Road Market | 09:00 | 2470.6 m (30.9m) | 46.4% | 2538.8 m (31.7m) | 51.1% | +68.2 m (+0.8 min) | **+4.7%** |
| Kamla Nehru Park ➔ FC Road Market | 13:00 | 2470.6 m (30.9m) | 26.5% | 2538.8 m (31.7m) | 30.1% | +68.2 m (+0.8 min) | **+3.6%** |
| Kamla Nehru Park ➔ FC Road Market | 16:00 | 2470.6 m (30.9m) | 48.4% | 2538.8 m (31.7m) | 53.4% | +68.2 m (+0.8 min) | **+5.0%** |
| Garware College ➔ MIT-WPU Campus | 09:00 | 3058.9 m (38.2m) | 37.5% | 3445.0 m (43.1m) | 61.1% | +386.1 m (+4.9 min) | **+23.6%** |
| Garware College ➔ MIT-WPU Campus | 13:00 | 3058.9 m (38.2m) | 21.7% | 3445.0 m (43.1m) | 39.2% | +386.1 m (+4.9 min) | **+17.5%** |
| Garware College ➔ MIT-WPU Campus | 16:00 | 3058.9 m (38.2m) | 40.6% | 3445.0 m (43.1m) | 65.9% | +386.1 m (+4.9 min) | **+25.3%** |


### Aggregate Performance
* **Mean Shade Gain**: +6.7% higher shade exposure on the Coolest path.
* **Mean Detour Distance**: +111.5 m.
* **Mean Detour Walking Time**: +1.4 minutes.
* **Conclusion**: Pedestrians gain substantial thermal relief with an average walking detour of under 2 minutes!

---

## Deliverables Completed
1. `scripts/day5_engine.py`: Enhanced arbitrary coordinate routing with dynamic Dijkstra weights.
2. `scripts/day5_server.py`: REST API server and static asset server on port 8050.
3. `web/index.html`: Responsive, accessible web UI structure.
4. `web/style.css`: Modern glassmorphic styling, dark theme, micro-animations, and comparison HUD.
5. `web/app.js`: Leaflet mapping, click-to-pin, landmark selection, live route rendering, and GeoJSON export.
6. `outputs/day5_map.html`: Standalone browser map.
7. `outputs/routes_day5.geojson`: Exported route geometries.

---

## How to Run the Web Application
```bash
# Start the Day 5 web server
python scripts/day5_server.py 8050

# Open in browser:
# http://127.0.0.1:8050
```
