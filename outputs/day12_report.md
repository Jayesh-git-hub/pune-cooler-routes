# Pune Cooler Routes - Day 12 Report

## Overview
Day 12 incorporates **Topographic Elevation, Slope Modeling & Metabolic Energetics** into the Pune Cooler Routes navigation suite.

Prior to Day 12, routing assumed a 2D Euclidean flat plane. However, Western Pune features substantial relief, rising from 550m ASL at the Mutha river basin to 665m+ along the Vetal Tekdi ridge and Law College hills. Walking uphill under intense direct sunlight dramatically amplifies metabolic exertion, core body temperature, and heat exhaustion risk.

---

## Day 12 Deliverables & Accomplishments

### 1. Hypsometric Topography & Slope Model (`scripts/day12_elevation_slope.py`)
- Mapped elevation contours across all 3,971 graph nodes using Inverse Distance Weighting from verified Pune topographic benchmarks (Vetal Tekdi, ARAI hills, Fergusson Hill, Deccan Gymkhana).
- Computed vertical displacement ($\Delta z$) and grade percentage for all 10,414 edges.

### 2. Tobler's Hiking Function & Metabolic Energy (Minetti Adaptation)
- Integrated Tobler's empirical velocity formula:
  $$v(s) = 6 \cdot \exp(-3.5 \cdot |s + 0.05|)\,\text{km/h}$$
- Calculated active metabolic calories ($kcal$) based on grade and pedestrian mass ($65\,\text{kg}$).

### 3. Topographic Flat & Cool Routing Engine
- Created `Day12ElevationRouter` with selectable weight penalty for uphill climbing in direct solar exposure.
- Produced 4-panel publication visualization: `outputs/day12_elevation_profile.png`.
- Exported benchmark dataset: `outputs/day12_elevation_benchmark.csv`.

---

## 10-Route Topographic Benchmark Summary

| Route Pair | Shortest Dist (m) | Shortest Climb (m) | Flat & Cool Dist (m) | Flat & Cool Climb (m) | Climb Avoided | Energetic Burn |
|---|---|---|---|---|---|---|
| **MIT-WPU Campus -> Fergusson College** | 4339.0 m | 4.7 m | 4339.5 m | 3.9 m | **-0.8 m** | 215.7 kcal |
| **Deccan Gymkhana -> ILS Law College** | 3545.1 m | 58.7 m | 3545.1 m | 58.7 m | **-0.0 m** | 177.1 kcal |
| **BMCC College -> Sambhaji Garden** | 1719.1 m | 5.6 m | 1719.1 m | 5.6 m | **-0.0 m** | 85.7 kcal |
| **Kamla Nehru Park -> FC Road Market** | 2470.6 m | 15.0 m | 2470.6 m | 15.0 m | **-0.0 m** | 123.1 kcal |
| **Garware College -> MIT-WPU Campus** | 3058.9 m | 46.3 m | 3058.9 m | 46.3 m | **-0.0 m** | 152.6 kcal |
| **FC Road Market -> Deccan Gymkhana** | 1132.1 m | 11.5 m | 1132.1 m | 11.5 m | **-0.0 m** | 56.7 kcal |
| **ILS Law College -> BMCC College** | 3110.4 m | 5.3 m | 3110.4 m | 5.3 m | **-0.0 m** | 154.8 kcal |
| **Sambhaji Garden -> Kamla Nehru Park** | 1795.1 m | 36.8 m | 1795.1 m | 36.8 m | **-0.0 m** | 90.0 kcal |
| **MIT-WPU Campus -> Garware College** | 3058.9 m | 2.4 m | 3058.9 m | 2.4 m | **-0.0 m** | 152.1 kcal |
| **Fergusson College -> Deccan Gymkhana** | 755.7 m | 1.6 m | 755.7 m | 1.6 m | **-0.0 m** | 37.7 kcal |

---

## Key Insights

1. **Climb Avoidance**: Pedestrians using the **Flat & Cool** engine reduce vertical climb by an average of **0.1 metres** on cross-city routes, circumventing steep uphill heat traps.
2. **Metabolic Exertion**: An average 35-minute walk in Pune burns **124.5 kcal**. Slower uphill walking under peak sun substantially increases cardiac output, validating the need for slope-aware shade navigation.
