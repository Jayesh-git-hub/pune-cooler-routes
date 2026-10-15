# Pune Cooler Routes - Day 8 Report

## Overview
Day 8 advances the **Pune Cooler Routes** navigation system beyond point-to-point routing into spatial reachability, network shade distribution, and live web overlays for Pune's pilot corridor (Kothrud, Karve Road, Deccan Gymkhana, FC Road).

---

## Day 8 Deliverables & Accomplishments

### 1. Network Shade Heatmap (`scripts/day8_shade_heatmap.py`)
- Analyzed all 10,414 edges across three daytime sun slots (09:00 morning, 13:00 peak midday, 16:00 late afternoon).
- Formulated a multi-slot **Composite Shade Score** weighted for midday heat stress:
  $$\text{Composite Shade} = 0.25 \times \text{shade}_{0900} + 0.50 \times \text{shade}_{1300} + 0.25 \times \text{shade}_{1600} + \text{tree\_bonus}$$
- Exported network heatmap GeoJSON (`outputs/day8_heatmap.geojson`) containing color-coded edge properties for Leaflet overlay.
- Generated 3-panel diurnal shade map (`outputs/day8_shade_heatmap.png`) and composite shade map (`outputs/day8_composite_shade.png`).
- Exported neighbourhood comparative rankings (`outputs/day8_neighbourhood_scores.csv`).

### 2. Shade-Aware Isochrone & Reachability Map (`scripts/day8_isochrone.py`)
- Computed 5, 10, and 15-minute walking isochrone rings centered at Deccan Gymkhana (18.5172°N, 73.8415°E).
- Evaluated dual isochrone models:
  - **Standard Walk Isochrone**: Traditional distance/speed reachable boundary.
  - **Shade-Priority Isochrone**: Biased towards cooler, canopy-covered corridors.
- Produced GeoJSON polygon contours:
  - `outputs/day8_isochrone_standard.geojson`
  - `outputs/day8_isochrone_shaded.geojson`
- Side-by-side reachability visual: `outputs/day8_isochrone_comparison.png`.
- Summary analysis: `outputs/day8_isochrone_report.md`.

### 3. Server & Web UI Integration (`scripts/day5_server.py`, `web/index.html`, `web/app.js`, `web/style.css`)
- Added Leaflet overlay toggles for:
  - **🌡️ Shade Heatmap Overlay**: Live choropleth layer on the map with custom tooltips showing morning, midday, afternoon shade percentages and tree bonus.
  - **⏱️ 5/10/15-min Isochrones**: Multi-ring shaded reachability contours.
- Added REST endpoints:
  - `GET /outputs/day8_heatmap.geojson`
  - `GET /outputs/day8_isochrone_shaded.geojson`
  - `GET /api/neighbourhood_scores`
  - `GET /api/shade_score?lat=...&lon=...`

---

## Key Results & Analytical Findings

### Neighbourhood Shade Ranking
| Neighbourhood | Composite Shade | Midday (13:00) | Tree Bonus | Edges Count | Tier |
|---|---|---|---|---|---|
| **Law College Rd** | **40.6%** | 27.7% | **+7.2%** | 548 | High Shade |
| **Senapati Bapat Marg** | **39.8%** | 27.2% | +6.5% | 1,270 | High Shade |
| **FC Road / Deccan** | **37.3%** | 25.4% | +3.5% | 3,204 | Moderate |
| **Prabhat Rd / JM Rd** | **36.1%** | 24.1% | +2.9% | 2,888 | Moderate |
| **Karve Road** | **35.8%** | 23.9% | +1.5% | 2,394 | Moderate |
| **Kothrud Core** | **33.9%** | 22.5% | +1.3% | 1,220 | Partial |

### Isochrone Reachability Analysis (from Deccan Gymkhana)
| Time Band | Standard Reachable Nodes | Standard % Well-Shaded | Shade-Priority Reachable Nodes | Shade-Priority % Well-Shaded | Improvement |
|---|---|---|---|---|---|
| **5 min** | 186 | 67.7% | 77 | 69.3% | +1.6% |
| **10 min** | 311 | 57.5% | 173 | **69.4%** | **+11.9%** |
| **15 min** | 344 | 54.7% | 211 | 56.6% | +1.9% |

> **Key Finding**: In the 10-minute pedestrian walking radius, biasing towards shaded paths increases the proportion of well-shaded corridor travel from **57.5% to 69.4% (+11.9% gain)**, ensuring significantly reduced thermal stress during routine commutes.
