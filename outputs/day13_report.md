# Pune Cooler Routes - Day 13 Report

## Overview
Day 13 solves a fundamental urban planning dilemma documented in **Loophole #18**: *pedestrians should not trade intense heat for heavy vehicular exhaust*. In Pune, major thoroughfares like Karve Road and Paud Road possess tall commercial buildings that cast shade, but concurrently expose walkers to intense diesel emissions, noise, and airborne particulates (PM2.5 / PM10).

Day 13 introduces the **Eco-Thermal Health Index (ETHI)** and clean-air biophilic routing, directing pedestrians along shaded, tranquil residential lanes with vegetative air purification.

---

## Day 13 Deliverables & Accomplishments

### 1. Vehicular Emission & Traffic Exhaust Model (`scripts/day13_air_quality.py`)
- Classified road hierarchies by empirical exhaust levels:
  - Primary / Trunk Arterials: 3.4–4.0 exhaust index (heavy stop-and-go diesel traffic).
  - Residential & Living Streets: 1.0–1.1 exhaust index (calm, low-speed).
  - Pedestrian & Green Paths: 0.75–0.85 exhaust index.
- Applied **Biophilic Tree Filtration Credits**: dense canopies filter up to **35% of particulate load**.

### 2. Clean & Cool Eco-Thermal Health Engine
- Formulated multi-objective routing function:
  $$\text{Cost} = \text{Length} \times [1 + w_{\text{shade}} (1 - \text{shade}) + w_{\text{air}} (\text{Exhaust} - 1.0)]$$
- Produced 4-panel publication visualization: `outputs/day13_air_thermal_tradeoff.png`.
- Exported benchmark dataset: `outputs/day13_clean_cool_routes.csv`.
- Added standard GPX GPS Exchange format track generator (`export_route_to_gpx`).

---

## 10-Route Clean-Air & Shade Benchmark Summary

| Route Pair | Fast Exhaust Index | Clean Exhaust Index | Exhaust Reduction | Fast Arterial % | Clean Arterial % | Arterial Avoided | Shade Gain |
|---|---|---|---|---|---|---|---|
| **MIT-WPU Campus -> Fergusson College** | 1.04 | 0.96 | **-7.7%** | 4.7% | 0.1% | **-4.6%** | +8.1% |
| **Deccan Gymkhana -> ILS Law College** | 0.93 | 0.93 | **-0.0%** | 0.4% | 0.4% | **-0.0%** | +0.0% |
| **BMCC College -> Sambhaji Garden** | 1.09 | 0.95 | **-12.8%** | 7.3% | 1.3% | **-6.0%** | +4.8% |
| **Kamla Nehru Park -> FC Road Market** | 1.89 | 1.04 | **-45.0%** | 34.3% | 0.2% | **-34.1%** | +26.7% |
| **Garware College -> MIT-WPU Campus** | 2.36 | 1.0 | **-57.6%** | 60.8% | 0.0% | **-60.8%** | +11.3% |
| **FC Road Market -> Deccan Gymkhana** | 3.26 | 1.09 | **-66.6%** | 94.5% | 0.8% | **-93.7%** | +29.3% |
| **ILS Law College -> BMCC College** | 0.96 | 0.96 | **-0.0%** | 0.2% | 0.2% | **-0.0%** | +0.3% |
| **Sambhaji Garden -> Kamla Nehru Park** | 2.76 | 1.0 | **-63.8%** | 76.9% | 1.1% | **-75.8%** | +22.9% |
| **MIT-WPU Campus -> Garware College** | 2.36 | 0.99 | **-58.1%** | 60.8% | 0.0% | **-60.8%** | +13.7% |
| **Fergusson College -> Deccan Gymkhana** | 2.81 | 1.41 | **-49.8%** | 77.1% | 19.9% | **-57.2%** | +38.1% |

---

## Key Findings

1. **Pollution Reduction**: The Clean & Cool engine slashes pedestrian vehicular exhaust exposure by an average of **36.1%**, actively guiding walkers away from congested bus and auto-rickshaw corridors.
2. **Highway Avoidance**: Drops high-traffic arterial walking from an average of 41.7% down to 2.4% (**-39.3% reduction**).
3. **Simultaneous Shade Advantage**: Achieves an additional **+15.5% shade gain** with only an average detour of **+324.2 metres**.
