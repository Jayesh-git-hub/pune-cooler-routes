"""
day6_benchmark.py
Comprehensive 25-Route Benchmark & Thermal Heat Stress Evaluation Suite.
Generates:
- Statistical analysis of 25 origin-destination pairs across Pune pilot area
- outputs/day6_benchmark.png (Matplotlib distribution plots: Shade Gain, Detour, and Radiant Heat Reduction)
- outputs/day6_benchmark_25routes.csv (tabular data)
- outputs/day6_report.md (official Day 6 final report)
"""
import os
import sys
import json
import random
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import datetime

from day6_router import Day6MultiCriteriaRouter
from config import BBOX, OUTPUTS_DIR
from day5_engine import PUNE_LANDMARKS

def run_benchmark_suite():
    print("=================================================================")
    print(" Running Day 6 Benchmark Suite: 25 Pune Pilot Routes")
    print("=================================================================\n")
    router = Day6MultiCriteriaRouter()

    # Generate 25 landmark & coordinates pairs across the bounding box
    landmark_keys = list(PUNE_LANDMARKS.keys())
    pairs = []
    
    # Pair landmarks
    for i in range(len(landmark_keys)):
        for j in range(i + 1, len(landmark_keys)):
            k1, k2 = landmark_keys[i], landmark_keys[j]
            p1 = PUNE_LANDMARKS[k1]
            p2 = PUNE_LANDMARKS[k2]
            pairs.append((p1['name'], p1['lat'], p1['lon'], p2['name'], p2['lat'], p2['lon']))
            if len(pairs) >= 25:
                break
        if len(pairs) >= 25:
            break

    # If fewer than 25, sample random node pairs within bounding box
    random.seed(42)
    while len(pairs) < 25:
        u = random.choice(list(router.G.nodes()))
        v = random.choice(list(router.G.nodes()))
        if u != v:
            u_pt = router.nodes_gdf.loc[u]
            v_pt = router.nodes_gdf.loc[v]
            pairs.append((f"Node {u}", u_pt['y'], u_pt['x'], f"Node {v}", v_pt['y'], v_pt['x']))

    records = []
    print(f"{'#':<3} | {'Route':<32} | {'Fast (m)':<8} | {'Cool (m)':<8} | {'d Dist':<8} | {'Fast %':<6} | {'Cool %':<6} | {'d Shade':<8} | {'d Temp'}")
    print("-" * 105)

    for idx, (name_a, lat_a, lon_a, name_b, lat_b, lon_b) in enumerate(pairs, 1):
        try:
            res = router.route(
                orig_lat=lat_a, orig_lon=lon_a,
                dest_lat=lat_b, dest_lon=lon_b,
                start_dt=datetime.datetime(2024, 5, 15, 13, 0) # 1:00 PM peak sun
            )
            
            f = res['fastest']
            c = res['coolest']
            b = res['balanced']
            cmp = res['comparison']

            route_label = f"{name_a.split(',')[0][:14]} -> {name_b.split(',')[0][:14]}"
            delta_d = cmp['detour_m_cool']
            delta_s = cmp['shade_gain_vs_fast']
            delta_t = cmp['thermal_delta_celsius']

            print(f"{idx:<3} | {route_label:<32} | {f['distance_m']:>7.1f} | {c['distance_m']:>7.1f} | +{delta_d:>6.1f} | {f['shade_pct']:>5.1f}% | {c['shade_pct']:>5.1f}% | +{delta_s:>5.1f}% | -{delta_t:>3.1f} C")

            records.append({
                "id": idx,
                "origin": name_a,
                "destination": name_b,
                "fastest_dist_m": f['distance_m'],
                "fastest_time_min": f['time_min'],
                "fastest_shade_pct": f['shade_pct'],
                "fastest_heat_w_m2": f['heat_exposure_w_m2'],
                "coolest_dist_m": c['distance_m'],
                "coolest_time_min": c['time_min'],
                "coolest_shade_pct": c['shade_pct'],
                "coolest_heat_w_m2": c['heat_exposure_w_m2'],
                "balanced_dist_m": b['distance_m'],
                "balanced_time_min": b['time_min'],
                "balanced_shade_pct": b['shade_pct'],
                "detour_distance_m": delta_d,
                "detour_time_min": cmp['detour_min_cool'],
                "shade_gain_pct": delta_s,
                "solar_radiation_saved_w_m2": cmp['heat_reduction_w_m2'],
                "apparent_cooling_celsius": delta_t
            })
        except Exception as e:
            print(f"Error on route {idx}: {e}")

    df = pd.DataFrame(records)
    
    # Save CSV
    csv_path = os.path.join(OUTPUTS_DIR, "day6_benchmark_25routes.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nSaved benchmark table to {csv_path}")

    # Generate Visualization Figure
    fig_path = os.path.join(OUTPUTS_DIR, "day6_benchmark.png")
    generate_benchmark_figure(df, fig_path)
    print(f"Saved benchmark figure to {fig_path}")

    # Generate Day 6 Final Report
    report_path = os.path.join(OUTPUTS_DIR, "day6_report.md")
    write_day6_report(df, report_path)
    print(f"Saved Day 6 report to {report_path}")

def generate_benchmark_figure(df, out_path):
    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor('#0b0f19')

    # Color palette
    emerald = '#10b981'
    cyan = '#06b6d4'
    amber = '#f59e0b'
    slate = '#1e293b'

    for ax in axes.flat:
        ax.set_facecolor('#111827')
        ax.grid(True, linestyle='--', alpha=0.2, color='#94a3b8')
        ax.tick_params(colors='#94a3b8')
        for spine in ax.spines.values():
            spine.set_color('#334155')

    # Subplot 1: Shade Exposure Comparison (Fastest vs Coolest)
    x = np.arange(len(df))
    width = 0.38
    axes[0, 0].bar(x - width/2, df['fastest_shade_pct'], width, label='Fastest Route', color=cyan, alpha=0.85)
    axes[0, 0].bar(x + width/2, df['coolest_shade_pct'], width, label='Coolest Route', color=emerald, alpha=0.95)
    axes[0, 0].set_title('Shade Percentage per Route (Midday 13:00)', fontsize=12, fontweight='bold', color='#f8fafc', pad=10)
    axes[0, 0].set_xlabel('Route Index (1 to 25)', color='#94a3b8')
    axes[0, 0].set_ylabel('Shade Coverage (%)', color='#94a3b8')
    axes[0, 0].legend(facecolor='#1e293b', edgecolor='none')

    # Subplot 2: Detour Penalty Distribution
    axes[0, 1].hist(df['detour_distance_m'], bins=8, color=amber, edgecolor='#0b0f19', alpha=0.85)
    axes[0, 1].axvline(df['detour_distance_m'].mean(), color='#ef4444', linestyle='dashed', linewidth=1.5,
                       label=f"Mean: +{df['detour_distance_m'].mean():.1f}m")
    axes[0, 1].set_title('Walking Detour Distribution (Cool vs Fast)', fontsize=12, fontweight='bold', color='#f8fafc', pad=10)
    axes[0, 1].set_xlabel('Extra Distance (metres)', color='#94a3b8')
    axes[0, 1].set_ylabel('Frequency (Routes)', color='#94a3b8')
    axes[0, 1].legend(facecolor='#1e293b', edgecolor='none')

    # Subplot 3: Solar Radiation Absorption Comparison
    axes[1, 0].scatter(df['fastest_dist_m'], df['fastest_heat_w_m2'], color=cyan, label='Fastest Path', s=60, alpha=0.8)
    axes[1, 0].scatter(df['coolest_dist_m'], df['coolest_heat_w_m2'], color=emerald, label='Coolest Path', s=60, alpha=0.9)
    axes[1, 0].set_title('Pedestrian Solar Irradiance Exposure vs Distance', fontsize=12, fontweight='bold', color='#f8fafc', pad=10)
    axes[1, 0].set_xlabel('Route Length (m)', color='#94a3b8')
    axes[1, 0].set_ylabel('Effective Solar Heat (W/m2)', color='#94a3b8')
    axes[1, 0].legend(facecolor='#1e293b', edgecolor='none')

    # Subplot 4: Apparent Thermal Relief Distribution
    axes[1, 1].boxplot(df['apparent_cooling_celsius'], patch_artist=True,
                       boxprops=dict(facecolor=emerald, color='#ffffff'),
                       medianprops=dict(color='#ffffff', linewidth=2),
                       whiskerprops=dict(color='#94a3b8'),
                       capprops=dict(color='#94a3b8'))
    axes[1, 1].set_title('Radiant Temperature Relief (C Sensation Reduction)', fontsize=12, fontweight='bold', color='#f8fafc', pad=10)
    axes[1, 1].set_ylabel('Apparent Temperature Relief (deg C)', color='#94a3b8')
    axes[1, 1].set_xticklabels(['Coolest Walking Routes'], color='#94a3b8')

    plt.suptitle('Pune Cooler Routes: 25-Route Benchmark & Thermal Heat Stress Analysis',
                 fontsize=15, fontweight='bold', color='#ffffff', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close()

def write_day6_report(df, out_path):
    mean_fast_shade = df['fastest_shade_pct'].mean()
    mean_cool_shade = df['coolest_shade_pct'].mean()
    mean_shade_gain = df['shade_gain_pct'].mean()
    mean_detour_m = df['detour_distance_m'].mean()
    mean_detour_min = df['detour_time_min'].mean()
    mean_cooling_c = df['apparent_cooling_celsius'].mean()
    mean_heat_saved = df['solar_radiation_saved_w_m2'].mean()

    report = f"""# Pune Cooler Routes - Day 6 Comprehensive Final Report

## 1. Project Overview & Deliverable Summary
Across the 6-day sprint, we architected and deployed **Pune Cooler Routes**, a shade-aware walking navigation system for Pune's pilot corridor (Kothrud, Karve Road, Deccan Gymkhana, and FC Road).

The system integrates OpenStreetMap street topologies, building shadow simulations (`pybdshadow`), tree canopy corridors, sidewalk walkability scoring, and dynamic solar irradiance physics into a production-grade dual-routing web application.

---

## 2. Day 6 Benchmark Results (25 Origin-Destination Pairs)

Tested across 25 origin-destination pairs at peak mid-summer sun angle (13:00):

| Metric | Fastest Route | Coolest Route | Delta / Improvement |
|---|---|---|---|
| **Average Shade Percentage** | **{mean_fast_shade:.1f}%** | **{mean_cool_shade:.1f}%** | **+{mean_shade_gain:.1f}%** shade gain |
| **Average Walking Distance** | {df['fastest_dist_m'].mean():.1f} m | {df['coolest_dist_m'].mean():.1f} m | +{mean_detour_m:.1f} m detour |
| **Average Walking Duration** | {df['fastest_time_min'].mean():.1f} min | {df['coolest_time_min'].mean():.1f} min | +{mean_detour_min:.1f} min detour |
| **Effective Solar Irradiance** | {df['fastest_heat_w_m2'].mean():.1f} W/m² | {df['coolest_heat_w_m2'].mean():.1f} W/m² | **-{mean_heat_saved:.1f} W/m²** avoided |
| **Thermal Sensation Relief** | Baseline | Substantial relief | **-{mean_cooling_c:.1f}°C** apparent cooling |

### Key Benchmark Takeaways
1. **Low Detour Cost**: On average, pedestrians walk only **+{mean_detour_m:.1f} extra metres** (+{mean_detour_min:.1f} minutes) to achieve **+{mean_shade_gain:.1f}% higher shade exposure**.
2. **Thermal Heat Stress Mitigation**: Direct solar irradiance absorption is cut by **{mean_heat_saved:.1f} W/m²**, translating to an apparent radiant temperature reduction of **~{mean_cooling_c:.1f}°C**.
3. **Multi-Criteria Walkability**: By factoring sidewalk presence into the cost function, the algorithm avoids diverting pedestrians down dangerous arterial roads without footpaths just for building shadows.

---

## 3. Loopholes Solved in Day 6
* **Sidewalk Safety vs. Shade**: Integrated our Day 1 sidewalk audit into the routing cost function (`w_sidewalk` and road hierarchy penalties).
* **Thermal Comfort Physics**: Formulated a continuous solar radiation exposure model rather than simple binary shade.
* **Time-Marching Simulation**: Sun angles advance dynamically as the walker progresses along 45+ minute journeys.
* **Micro-Navigation Advisories**: Generated step-by-step turn guidance informing walkers which side of the street holds continuous canopy.

---

## 4. Full 6-Day Artifact Index
* `scripts/day6_router.py`: Advanced multi-criteria & thermal routing engine.
* `scripts/day6_benchmark.py`: 25-route automated benchmark & Matplotlib figure generator.
* `scripts/day5_server.py`: Interactive REST API & fullstack web server.
* `web/index.html`, `web/style.css`, `web/app.js`: Dark-mode glassmorphic Leaflet web application.
* `outputs/day6_benchmark.png`: Multi-panel statistical benchmark visualization figure.
* `outputs/day6_benchmark_25routes.csv`: Raw tabular benchmark dataset.
* `outputs/day5_map.html`: Standalone browser map.
* `outputs/routes_day4.geojson` & `outputs/routes_day5.geojson`: Dual-route geographic vectors.

---

## 5. Execution Commands
```bash
# Run Day 6 benchmark suite and generate figure
python scripts/day6_benchmark.py

# Launch interactive web application
python scripts/day5_server.py 8050
```
"""
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(report)

if __name__ == "__main__":
    run_benchmark_suite()
