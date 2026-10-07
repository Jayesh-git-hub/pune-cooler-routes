"""
day4_router.py  -  reads the fixed edges_shaded.gpkg and runs routing.
Fastest = Dijkstra on raw length.
Coolest = Dijkstra on shade-inflated cool_weight.
Loophole fixes:
  - Dynamic time: picks shade snapshot nearest to current hour
  - Sidewalk safety: motorway/trunk edges penalised 3x
"""
import os
import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
import datetime
from shapely.geometry import LineString
from config import PT_MIT_WPU, PT_FC, WALKING_SPEED_KMH, DATA_PROCESSED_DIR, OUTPUTS_DIR

SHADE_WEIGHT = 2.0   # multiplier: sunny edge costs 1+2=3x more than shaded


def shade_col_for_hour(hour):
    if hour < 11:  return 'shade_frac_0900'
    elif hour < 15: return 'shade_frac_1300'
    else:           return 'shade_frac_1600'


def build_graph_with_shade(hour):
    G = ox.load_graphml(filepath=os.path.join(DATA_PROCESSED_DIR, "network.graphml"))
    shaded = gpd.read_file(os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg"))
    col = shade_col_for_hour(hour)
    print(f"Using shade column: {col}")

    # Build lookup: (u, v, key) -> shade_frac
    lookup = {}
    for _, row in shaded.iterrows():
        k = (int(row['u']), int(row['v']), int(row['key']))
        lookup[k] = float(row.get(col, 0.0) or 0.0)

    for u, v, k, data in G.edges(keys=True, data=True):
        sf = lookup.get((u, v, k), lookup.get((v, u, k), 0.0))
        data['shade_frac'] = sf
        sun_frac = max(0.0, 1.0 - sf)
        length = data.get('length', 1.0)
        cool_w = length * (1.0 + SHADE_WEIGHT * sun_frac)
        # Penalise dangerous fast roads with no footpaths
        hw = data.get('highway', '')
        if isinstance(hw, list): hw = hw[0] if hw else ''
        if hw in ('motorway', 'trunk', 'motorway_link', 'trunk_link'):
            cool_w *= 3.0
        data['cool_weight'] = cool_w
    return G


def route_stats(G, route, col):
    total = shaded = 0.0
    for u, v in zip(route[:-1], route[1:]):
        d = G[u][v][0]
        seg = d.get('length', 0.0)
        sf  = d.get('shade_frac', 0.0) or 0.0
        total  += seg
        shaded += seg * sf
    time_min  = (total / 1000) / WALKING_SPEED_KMH * 60
    shade_pct = (shaded / total * 100) if total else 0.0
    return round(total, 1), round(time_min, 1), round(shade_pct, 1)


def street_names(G, route):
    names = []
    for u, v in zip(route[:-1], route[1:]):
        n = G[u][v][0].get('name', 'Unnamed')
        if isinstance(n, list): n = ', '.join(n)
        if not names or n != names[-1]: names.append(n)
    return names


def to_gdf(G, route, label):
    nodes_gdf, _ = ox.graph_to_gdfs(G)
    pts = [nodes_gdf.loc[nd, 'geometry'] for nd in route]
    return gpd.GeoDataFrame({'route': [label]}, geometry=[LineString(pts)], crs="EPSG:4326")


def main():
    now  = datetime.datetime.now()
    hour = now.hour
    col  = shade_col_for_hour(hour)
    print(f"Pune Cooler Routes - Day 4\nTime: {now.strftime('%H:%M')} -> using {col}\n")

    G    = build_graph_with_shade(hour)
    orig = ox.distance.nearest_nodes(G, X=PT_MIT_WPU[1], Y=PT_MIT_WPU[0])
    dest = ox.distance.nearest_nodes(G, X=PT_FC[1],      Y=PT_FC[0])

    print("Computing FASTEST route...")
    fastest = nx.shortest_path(G, orig, dest, weight='length')
    fd, ft, fs = route_stats(G, fastest, col)
    print(f"  {fd} m  |  {ft} min  |  {fs}% shade")
    print(f"  {', '.join(street_names(G, fastest))}\n")

    print("Computing COOLEST route...")
    coolest = nx.shortest_path(G, orig, dest, weight='cool_weight')
    cd, ct, cs = route_stats(G, coolest, col)
    print(f"  {cd} m  |  {ct} min  |  {cs}% shade")
    print(f"  {', '.join(street_names(G, coolest))}\n")

    extra_m   = round(cd - fd, 1)
    extra_min = round(ct - ft, 1)
    shade_gain= round(cs - fs, 1)
    print(f"=== TRADEOFF: +{extra_m} m / +{extra_min} min for +{shade_gain}% shade ===")

    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    gdf = pd.concat([to_gdf(G, fastest, 'fastest'),
                     to_gdf(G, coolest, 'coolest')], ignore_index=True)
    out_json = os.path.join(OUTPUTS_DIR, "routes_day4.geojson")
    gdf.to_file(out_json, driver="GeoJSON")
    print(f"Saved routes to {out_json}")

    report = f"""# Pune Cooler Routes - Day 4 Report

## What We Built
A dual-route engine computing two walking paths from MIT-WPU to Fergusson College:
- **Fastest Route**: Dijkstra on raw edge length.
- **Coolest Route**: Dijkstra on cool_weight (shade-inflated cost + road safety penalty).

## Loophole Fixes Applied
1. **Dynamic Time**: Picks shade snapshot nearest to current hour ({hour:02d}:00).
2. **Sidewalk Safety**: motorway/trunk edges get a 3x cost penalty.
3. **Tree Canopies**: included in shadow casting from Day 3.

## Results (run at {now.strftime('%H:%M IST')})

| | Fastest | Coolest |
|---|---|---|
| Distance | {fd} m | {cd} m |
| Walking Time | {ft} min | {ct} min |
| Avg Shade | {fs}% | {cs}% |

**Tradeoff**: Coolest adds {extra_m} m ({extra_min} min) but gains {shade_gain}% more shade.

## Output Files
- `outputs/routes_day4.geojson` - both routes ready for web map display.
"""
    out_report = os.path.join(OUTPUTS_DIR, "day4_report.md")
    with open(out_report, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Saved report to {out_report}")


if __name__ == "__main__":
    main()
