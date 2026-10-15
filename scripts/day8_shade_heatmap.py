"""
day8_shade_heatmap.py
Day 8: Shade Heatmap Generator for Pune Cooler Routes.

Generates:
1. A dark-theme choropleth map of the pilot area coloured by shade_frac at each time slot.
2. A combined composite shade score (weighted average of all 3 time slots).
3. GeoJSON file for heatmap overlay in the web app.
4. Separate neighbourhood-level shade summary.

Outputs:
  - outputs/day8_shade_heatmap.png       (3-panel dark map: 09:00 / 13:00 / 16:00)
  - outputs/day8_composite_shade.png     (single composite score map)
  - outputs/day8_heatmap.geojson         (all edges with shade scores, for Leaflet overlay)
  - outputs/day8_neighbourhood_scores.csv (neighbourhood-level shade summary)
"""
import os, sys, json, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from shapely.geometry import mapping

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from config import DATA_PROCESSED_DIR, OUTPUTS_DIR, BBOX

# Weights for composite shade score (morning + peak + afternoon)
SLOT_WEIGHTS = {"shade_frac_0900": 0.25, "shade_frac_1300": 0.50, "shade_frac_1600": 0.25}

BG_COLOR   = "#0f0f23"
TXT_COLOR  = "#e2e8f0"
GRID_COLOR = "#1e2a3a"

# Pune neighbourhood bounding boxes (name, west, south, east, north)
NEIGHBOURHOODS = [
    ("FC Road / Deccan",    73.830, 18.510, 73.846, 18.531),
    ("Senapati Bapat Marg", 73.820, 18.508, 73.835, 18.525),
    ("Law College Rd",      73.822, 18.508, 73.832, 18.518),
    ("Karve Road",          73.802, 18.495, 73.820, 18.515),
    ("Kothrud Core",        73.802, 18.495, 73.815, 18.510),
    ("Prabhat Rd / JM Rd",  73.830, 18.500, 73.846, 18.516),
]


def load_edges():
    path = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
    gdf = gpd.read_file(path)
    for col in ["shade_frac_0900", "shade_frac_1300", "shade_frac_1600", "tree_shade_bonus"]:
        gdf[col] = pd.to_numeric(gdf[col], errors="coerce").fillna(0.0)
    # Composite shade: weighted average + tree bonus
    gdf["composite_shade"] = (
        gdf["shade_frac_0900"] * SLOT_WEIGHTS["shade_frac_0900"] +
        gdf["shade_frac_1300"] * SLOT_WEIGHTS["shade_frac_1300"] +
        gdf["shade_frac_1600"] * SLOT_WEIGHTS["shade_frac_1600"] +
        gdf["tree_shade_bonus"] * 0.15
    ).clip(0.0, 1.0)
    print(f"Loaded {len(gdf):,} edges.")
    print(f"  Composite shade: mean={gdf['composite_shade'].mean():.3f}, max={gdf['composite_shade'].max():.3f}")
    return gdf


def plot_3panel_heatmap(gdf):
    """3-panel map: shade at 09:00 / 13:00 / 16:00 side-by-side."""
    slots = [
        ("shade_frac_0900", "09:00 Morning Sun",   "YlOrRd_r"),
        ("shade_frac_1300", "13:00 Midday Sun",    "RdYlGn"),
        ("shade_frac_1600", "shade_frac_1600", "16:00 Afternoon Sun", "YlGn"),
    ]
    slots = [
        ("shade_frac_0900", "09:00 Morning Sun",   "YlGn"),
        ("shade_frac_1300", "13:00 Midday Sun",    "RdYlGn"),
        ("shade_frac_1600", "16:00 Afternoon Sun", "YlGn"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(22, 9))
    fig.patch.set_facecolor(BG_COLOR)
    fig.suptitle(
        "Day 8 · Pune Pilot Area — Road Shade Fraction by Time of Day",
        fontsize=16, fontweight="bold", color=TXT_COLOR, y=1.02
    )

    for ax, (col, title, cmap) in zip(axes, slots):
        ax.set_facecolor(BG_COLOR)
        ax.tick_params(colors=TXT_COLOR, labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_COLOR)

        norm = mcolors.Normalize(vmin=0, vmax=1)
        gdf.plot(ax=ax, column=col, cmap=cmap, norm=norm, linewidth=0.7, alpha=0.88)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.04, pad=0.04)
        cbar.set_label("Shade Fraction (0=Sun, 1=Full Shade)", color=TXT_COLOR, fontsize=8)
        cbar.ax.yaxis.set_tick_params(color=TXT_COLOR)
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TXT_COLOR)

        mean_s = gdf[col].mean()
        ax.set_title(
            f"{title}\nNetwork Mean: {mean_s*100:.1f}% Shade",
            fontsize=11, fontweight="bold", color=TXT_COLOR, pad=10
        )
        ax.set_xlabel("Longitude", color=TXT_COLOR, fontsize=8)
        ax.set_ylabel("Latitude", color=TXT_COLOR, fontsize=8)

    plt.tight_layout()
    out = os.path.join(OUTPUTS_DIR, "day8_shade_heatmap.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    print(f"  Saved: {out}")
    return out


def plot_composite_map(gdf):
    """Single composite shade score map with neighbourhood annotations."""
    fig, ax = plt.subplots(figsize=(14, 11))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TXT_COLOR, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)

    cmap = "RdYlGn"
    norm = mcolors.Normalize(vmin=0, vmax=1)
    gdf.plot(ax=ax, column="composite_shade", cmap=cmap, norm=norm, linewidth=1.0, alpha=0.90)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("Composite Shade Score (0=Full Sun, 1=Always Shaded)", color=TXT_COLOR, fontsize=9)
    cbar.ax.yaxis.set_tick_params(color=TXT_COLOR)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TXT_COLOR)

    # Annotate neighbourhood labels
    nb_data = compute_neighbourhood_scores(gdf)
    for _, row in nb_data.iterrows():
        cx = (row["west"] + row["east"]) / 2
        cy = (row["south"] + row["north"]) / 2
        score = row["composite_shade"]
        color = "#10b981" if score > 0.45 else ("#f59e0b" if score > 0.35 else "#ef4444")
        ax.annotate(
            f"{row['neighbourhood']}\n{score*100:.0f}%",
            xy=(cx, cy), ha="center", va="center",
            fontsize=7.5, fontweight="bold", color=color,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#0f0f23", edgecolor=color, alpha=0.85)
        )

    ax.set_title(
        "Day 8 · Composite Shade Score Map — Pune Pilot Area\n"
        "Weighted Average: 25% Morning + 50% Midday + 25% Afternoon + 15% Tree Canopy Bonus",
        fontsize=13, fontweight="bold", color=TXT_COLOR, pad=14
    )
    ax.set_xlabel("Longitude", color=TXT_COLOR)
    ax.set_ylabel("Latitude", color=TXT_COLOR)

    plt.tight_layout()
    out = os.path.join(OUTPUTS_DIR, "day8_composite_shade.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    print(f"  Saved: {out}")
    return out


def compute_neighbourhood_scores(gdf):
    """Compute mean shade metrics for each neighbourhood polygon."""
    records = []
    gdf_wgs = gdf.to_crs("EPSG:4326") if gdf.crs and gdf.crs.to_epsg() != 4326 else gdf

    for name, west, south, east, north in NEIGHBOURHOODS:
        cx = (west + east) / 2
        cy = (south + north) / 2
        mask = (
            (gdf_wgs.geometry.centroid.x >= west) &
            (gdf_wgs.geometry.centroid.x <= east) &
            (gdf_wgs.geometry.centroid.y >= south) &
            (gdf_wgs.geometry.centroid.y <= north)
        )
        subset = gdf_wgs[mask]
        if len(subset) == 0:
            continue
        records.append({
            "neighbourhood": name,
            "west": west, "south": south, "east": east, "north": north,
            "edges_count": len(subset),
            "shade_frac_0900": round(subset["shade_frac_0900"].mean(), 4),
            "shade_frac_1300": round(subset["shade_frac_1300"].mean(), 4),
            "shade_frac_1600": round(subset["shade_frac_1600"].mean(), 4),
            "tree_bonus": round(subset["tree_shade_bonus"].mean(), 4),
            "composite_shade": round(subset["composite_shade"].mean(), 4),
        })

    df = pd.DataFrame(records).sort_values("composite_shade", ascending=False)
    out = os.path.join(OUTPUTS_DIR, "day8_neighbourhood_scores.csv")
    df.to_csv(out, index=False)
    print(f"  Saved neighbourhood scores: {out}")
    return df


def export_heatmap_geojson(gdf):
    """Export edges as GeoJSON FeatureCollection with shade data for Leaflet overlay."""
    features = []
    gdf_wgs = gdf.to_crs("EPSG:4326") if gdf.crs and gdf.crs.to_epsg() != 4326 else gdf

    for _, row in gdf_wgs.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue
        name_val = row.get("name", "")
        if isinstance(name_val, list):
            name_val = ", ".join(str(n) for n in name_val if n)
        features.append({
            "type": "Feature",
            "properties": {
                "name": str(name_val) if name_val else "Unnamed",
                "highway": str(row.get("highway", "")),
                "shade_0900": round(float(row["shade_frac_0900"]), 4),
                "shade_1300": round(float(row["shade_frac_1300"]), 4),
                "shade_1600": round(float(row["shade_frac_1600"]), 4),
                "tree_bonus": round(float(row["tree_shade_bonus"]), 4),
                "composite":  round(float(row["composite_shade"]), 4),
                "length_m":   round(float(row.get("length", 0.0)), 1),
            },
            "geometry": mapping(row.geometry)
        })

    geojson = {"type": "FeatureCollection", "features": features}
    out = os.path.join(OUTPUTS_DIR, "day8_heatmap.geojson")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(geojson, f, separators=(",", ":"))
    size_mb = os.path.getsize(out) / 1024 / 1024
    print(f"  Saved heatmap GeoJSON: {out}  ({size_mb:.2f} MB, {len(features):,} features)")
    return out


if __name__ == "__main__":
    print("=" * 60)
    print("  Pune Cooler Routes - Day 8 Shade Heatmap Generator")
    print("=" * 60)

    gdf = load_edges()

    print("\n[1/4] Generating 3-panel time-of-day heatmap...")
    plot_3panel_heatmap(gdf)

    print("\n[2/4] Generating composite shade score map...")
    plot_composite_map(gdf)

    print("\n[3/4] Computing neighbourhood shade scores...")
    nb = compute_neighbourhood_scores(gdf)
    print(nb[["neighbourhood", "edges_count", "composite_shade"]].to_string(index=False))

    print("\n[4/4] Exporting heatmap GeoJSON for Leaflet overlay...")
    export_heatmap_geojson(gdf)

    print("\n" + "=" * 60)
    print("  Day 8 Shade Heatmap Complete!")
    print("=" * 60)
