"""
day9_smart_planner.py
Day 9: Smart Waypoint Planner for Pune Cooler Routes.

Given an origin and destination, finds the BEST single intermediate waypoint
that maximises shade gain with minimal detour overhead.

Algorithm:
  1. Compute direct Coolest route (no waypoint).
  2. For each candidate intermediate landmark / street centroid:
       a. Route: Origin -> Waypoint -> Destination (using shade_cost)
       b. Compute shade gain vs direct coolest, and detour distance/time.
  3. Rank candidates by: shade_gain / max(1, detour_m / 100)
  4. Return top-5 recommendations.

Outputs:
  - outputs/day9_waypoint_recommendations.csv
  - outputs/day9_smart_planner.png  (visualisation of top-3 waypoint routes)
  - outputs/day9_smart_planner_report.md
"""
import os, sys, json, warnings
warnings.filterwarnings("ignore")

import datetime
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
import osmnx as ox
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from config import DATA_PROCESSED_DIR, OUTPUTS_DIR, WALKING_SPEED_KMH
from day5_engine import PUNE_LANDMARKS

WALKING_SPEED_M_PER_MIN = (WALKING_SPEED_KMH * 1000.0) / 60.0
BG  = "#0f0f23"
TXT = "#e2e8f0"

# Default test: MIT-WPU -> Fergusson College (longest known route in pilot area)
DEFAULT_ORIGIN = PUNE_LANDMARKS["mit_wpu"]
DEFAULT_DEST   = PUNE_LANDMARKS["fergusson"]

# Candidate intermediate points: a curated list of named shady spots
CANDIDATE_WAYPOINTS = [
    {"id": "bhandarkar",   "name": "Bhandarkar Rd / Kelkar Rd Junction", "lat": 18.5138, "lon": 73.8358},
    {"id": "law_college",  "name": "ILS Law College Gate",               "lat": 18.5165, "lon": 73.8268},
    {"id": "senapati",     "name": "Senapati Bapat Marg Midpoint",       "lat": 18.5100, "lon": 73.8251},
    {"id": "prabhat",      "name": "Prabhat Road (Tree Corridor)",       "lat": 18.5118, "lon": 73.8336},
    {"id": "jm_road",      "name": "JM Road / University Corner",        "lat": 18.5155, "lon": 73.8383},
    {"id": "agarkar",      "name": "Gopal Ganesh Agarkar Path",          "lat": 18.5190, "lon": 73.8333},
    {"id": "chiplunkar",   "name": "Vishnushastri Chiplunkar Path",      "lat": 18.5208, "lon": 73.8295},
    {"id": "karve_nal_st", "name": "Karve Nagar (Nal Stop)",            "lat": 18.4998, "lon": 73.8220},
    {"id": "sambhaji_gdn", "name": "Chhatrapati Sambhaji Garden Adj.",   "lat": 18.5192, "lon": 73.8471},
    {"id": "fc_trees",     "name": "FC Road (Wrangler P.R. Bhagwat Path)", "lat": 18.5256, "lon": 73.8397},
    {"id": "bmcc_gate",    "name": "BMCC College Road",                 "lat": 18.5218, "lon": 73.8340},
    {"id": "deccan",       "name": "Deccan Gymkhana",                   "lat": 18.5172, "lon": 73.8415},
]


def load_graph_and_shade():
    graphml_path = os.path.join(DATA_PROCESSED_DIR, "network.graphml")
    shaded_path  = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
    G   = ox.load_graphml(filepath=graphml_path)
    gdf = gpd.read_file(shaded_path)

    for col in ["shade_frac_0900", "shade_frac_1300", "shade_frac_1600", "tree_shade_bonus"]:
        gdf[col] = pd.to_numeric(gdf[col], errors="coerce").fillna(0.0)

    gdf["composite_shade"] = (
        gdf["shade_frac_0900"] * 0.25 +
        gdf["shade_frac_1300"] * 0.50 +
        gdf["shade_frac_1600"] * 0.25 +
        gdf["tree_shade_bonus"] * 0.15
    ).clip(0, 1)

    shade_lut = {}
    for _, row in gdf.iterrows():
        k = (int(row["u"]), int(row["v"]), int(row["key"]))
        shade_lut[k] = {
            "shade_1300": float(row["shade_frac_1300"]),
            "tree_bonus": float(row["tree_shade_bonus"]),
            "composite":  float(row["composite_shade"]),
        }

    # Inject edge weights
    for u, v, k, d in G.edges(keys=True, data=True):
        meta = shade_lut.get((u, v, k), shade_lut.get((v, u, k), {}))
        sf   = meta.get("shade_1300", 0.25)
        length = float(d.get("length", 1.0))
        sun = max(0.0, 1.0 - sf)
        d["shade_cost"] = length * (1.0 + 2.5 * sun)
        d["composite"]  = meta.get("composite", 0.25)

    return G, shade_lut


def route_shade_stats(G, path, shade_lut):
    """Return (distance_m, time_min, mean_composite_shade) for a path."""
    total_dist = 0.0
    shade_weighted = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        d = G[u][v][0]
        seg_len = float(d.get("length", 0.0))
        total_dist += seg_len
        meta = shade_lut.get((u, v, 0), shade_lut.get((v, u, 0), {}))
        shade_weighted += seg_len * meta.get("composite", 0.25)
    mean_shade = shade_weighted / total_dist if total_dist > 0 else 0.0
    time_min   = (total_dist / 1000.0) / WALKING_SPEED_KMH * 60.0
    return round(total_dist, 1), round(time_min, 1), round(mean_shade, 4)


def path_coordinates(G, path):
    """Return list of [lat, lon] coords."""
    nodes_gdf, _ = ox.graph_to_gdfs(G)
    coords = []
    for node in path:
        row = nodes_gdf.loc[node]
        coords.append([float(row["y"]), float(row["x"])])
    return coords


def evaluate_waypoints(G, shade_lut, orig_lat, orig_lon, dest_lat, dest_lon):
    """Evaluate all candidate waypoints and score them."""
    # Snap origin & destination
    orig_node = ox.distance.nearest_nodes(G, X=orig_lon, Y=orig_lat)
    dest_node = ox.distance.nearest_nodes(G, X=dest_lon, Y=dest_lat)

    # Direct coolest route (no waypoint)
    direct_path = nx.shortest_path(G, orig_node, dest_node, weight="shade_cost")
    direct_dist, direct_time, direct_shade = route_shade_stats(G, direct_path, shade_lut)
    print(f"  Direct coolest route: {direct_dist}m | {direct_time}min | shade={direct_shade*100:.1f}%")

    results = []
    for wp in CANDIDATE_WAYPOINTS:
        wp_node = ox.distance.nearest_nodes(G, X=wp["lon"], Y=wp["lat"])
        if wp_node == orig_node or wp_node == dest_node:
            continue
        try:
            path_a = nx.shortest_path(G, orig_node, wp_node, weight="shade_cost")
            path_b = nx.shortest_path(G, wp_node, dest_node, weight="shade_cost")
        except nx.NetworkXNoPath:
            continue

        # Combine paths (avoid duplicating waypoint node)
        full_path = path_a + path_b[1:]
        dist, time, shade = route_shade_stats(G, full_path, shade_lut)

        shade_gain   = shade - direct_shade
        detour_m     = max(0.0, dist - direct_dist)
        detour_min   = max(0.0, time - direct_time)

        # Score: shade gain per 100m of detour (higher = better)
        score = (shade_gain * 100.0) / max(1.0, detour_m / 100.0)

        results.append({
            "waypoint_id":    wp["id"],
            "waypoint_name":  wp["name"],
            "waypoint_lat":   wp["lat"],
            "waypoint_lon":   wp["lon"],
            "total_dist_m":   dist,
            "total_time_min": time,
            "mean_shade_pct": round(shade * 100, 1),
            "shade_gain_pct": round(shade_gain * 100, 1),
            "detour_m":       round(detour_m, 1),
            "detour_min":     round(detour_min, 1),
            "score":          round(score, 4),
            "full_path":      full_path,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return direct_path, direct_dist, direct_time, direct_shade, results


def save_results(results, direct_shade, direct_dist):
    """Save top recommendations to CSV."""
    rows = []
    for r in results[:10]:
        rows.append({
            "rank": len(rows) + 1,
            "waypoint":        r["waypoint_name"],
            "total_dist_m":    r["total_dist_m"],
            "total_time_min":  r["total_time_min"],
            "shade_pct":       r["mean_shade_pct"],
            "shade_gain_pct":  r["shade_gain_pct"],
            "detour_m":        r["detour_m"],
            "detour_min":      r["detour_min"],
            "score":           r["score"],
        })
    df = pd.DataFrame(rows)
    out = os.path.join(OUTPUTS_DIR, "day9_waypoint_recommendations.csv")
    df.to_csv(out, index=False)
    print(f"  Saved: {out}")
    return df


def plot_top3(G, direct_path, results, orig, dest):
    """Plot top-3 waypoint routes vs direct coolest route."""
    nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)
    top3 = results[:3]

    fig, axes = plt.subplots(1, min(4, len(top3) + 1), figsize=(22, 10))
    if not hasattr(axes, "__iter__"):
        axes = [axes]
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"Day 9 · Smart Waypoint Planner: Top-3 Shade-Boosted Routes\n"
        f"Origin: {orig['name']}  →  Destination: {dest['name']}",
        fontsize=13, fontweight="bold", color=TXT, y=1.01
    )

    route_colors = ["#10b981", "#a78bfa", "#f59e0b"]
    panels = [("Direct Coolest\n(No Waypoint)", direct_path, "#06b6d4")] + \
             [(f"Via {r['waypoint_name'][:30]}\n+{r['shade_gain_pct']:.1f}% shade | +{r['detour_m']:.0f}m",
               r["full_path"], route_colors[i]) for i, r in enumerate(top3)]

    for ax, (title, path, color) in zip(axes, panels):
        ax.set_facecolor(BG)
        ax.tick_params(colors=TXT, labelsize=6)
        for spine in ax.spines.values():
            spine.set_edgecolor("#1e2a3a")

        # Base network
        edges_gdf.plot(ax=ax, color="#1e2a3a", linewidth=0.4, alpha=0.5)

        # Route polyline
        coords = path_coordinates(G, path)
        if coords:
            lons = [c[1] for c in coords]
            lats = [c[0] for c in coords]
            ax.plot(lons, lats, color=color, linewidth=3.5, alpha=0.9, zorder=5)

        # Origin / destination markers
        ax.plot(orig["lon"], orig["lat"], "o", color="#10b981", markersize=10, zorder=6)
        ax.plot(dest["lon"], dest["lat"], "o", color="#ef4444",  markersize=10, zorder=6)

        ax.set_title(title, fontsize=9, fontweight="bold", color=TXT, pad=8)
        ax.set_xlabel("Longitude", color=TXT, fontsize=7)

    plt.tight_layout()
    out = os.path.join(OUTPUTS_DIR, "day9_smart_planner.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"  Saved: {out}")
    return out


def write_report(df, direct_shade, direct_dist, direct_time, orig, dest):
    """Write a Markdown smart planner report."""
    lines = [
        "# Day 9 Smart Waypoint Planner Report",
        "",
        f"**Origin**: {orig['name']} ({orig['lat']}°N, {orig['lon']}°E)",
        f"**Destination**: {dest['name']} ({dest['lat']}°N, {dest['lon']}°E)",
        "",
        f"**Direct Coolest Route** (no waypoint): {direct_dist}m | {direct_time}min | {direct_shade*100:.1f}% shade",
        "",
        "---",
        "",
        "## Top Waypoint Recommendations",
        "",
        df.to_markdown(index=False),
        "",
        "---",
        "",
        "## How to Read This Table",
        "- **shade_gain_pct**: Extra percentage of shade compared to the direct coolest route.",
        "- **detour_m / detour_min**: Extra distance and time cost of taking the waypoint.",
        "- **score**: Shade gain per 100m of detour — higher is a better deal.",
        "",
        "## Interpretation",
        "",
    ]
    if len(df) > 0:
        top = df.iloc[0]
        lines += [
            f"The **best waypoint** is **{top['waypoint']}**:",
            f"  - Adds **+{top['shade_gain_pct']:.1f}%** more shade coverage",
            f"  - Costs only **+{top['detour_m']:.0f} m** extra walking ({top['detour_min']:.1f} extra min)",
            f"  - Shade score: {top['shade_pct']:.1f}% of the route is under tree/building shade",
        ]
    lines += [
        "",
        "> **Day 9 Deliverables**: `day9_waypoint_recommendations.csv`, `day9_smart_planner.png`,",
        "> `day9_smart_planner_report.md`",
    ]
    out = os.path.join(OUTPUTS_DIR, "day9_smart_planner_report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Saved: {out}")
    return out


if __name__ == "__main__":
    print("=" * 60)
    print("  Pune Cooler Routes - Day 9 Smart Waypoint Planner")
    print("=" * 60)

    print("\nLoading graph + shade data...")
    G, shade_lut = load_graph_and_shade()

    orig = DEFAULT_ORIGIN
    dest = DEFAULT_DEST
    print(f"Route: {orig['name']}  ->  {dest['name']}")

    print("\n[1/3] Evaluating all candidate waypoints...")
    direct_path, direct_dist, direct_time, direct_shade, results = evaluate_waypoints(
        G, shade_lut, orig["lat"], orig["lon"], dest["lat"], dest["lon"]
    )

    print(f"\n  Evaluated {len(results)} waypoints.")
    if results:
        print("  Top-5 waypoints by score:")
        for r in results[:5]:
            print(f"    [{r['score']:+.3f}] {r['waypoint_name'][:40]:40s}  "
                  f"shade_gain={r['shade_gain_pct']:+.1f}%  detour={r['detour_m']:+.0f}m")

    print("\n[2/3] Saving recommendations CSV...")
    df = save_results(results, direct_shade, direct_dist)

    print("\n[3/3] Plotting top-3 waypoint routes...")
    plot_top3(G, direct_path, results, orig, dest)
    write_report(df, direct_shade, direct_dist, direct_time, orig, dest)

    print("\n" + "=" * 60)
    print("  Day 9 Smart Waypoint Planner Complete!")
    print("=" * 60)
