"""
day7_canopy_offline.py
Day 7 (Offline): Tree canopy bonus estimation without OSM download.

When the OSM Overpass API is unavailable, this script assigns tree_shade_bonus
values to every road edge using two offline heuristics:

  1. KNOWN-CANOPY STREETS: Pune streets historically documented as having
     dense old-growth tree canopy (FC Road, Bhandarkar, Senapati Bapat,
     Law College Rd etc.). These get a base bonus of 0.35-0.55.

  2. SHADE-FRACTION PROXY: Edges that already have high building-shadow
     shade_frac values (>= 0.50) are likely near tall vegetation too, so
     they receive a proportional canopy bonus.

  Combined bonus = max(name_bonus, shade_proxy) capped at 1.0.

Outputs:
  - data/processed/edges_shaded.gpkg  (with tree_shade_bonus column)
  - outputs/day7_canopy_map.png        (road network coloured by bonus)
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from config import DATA_PROCESSED_DIR, OUTPUTS_DIR, BBOX

# Streets in Pune's pilot area known for dense tree canopy
# (FC Road, Bhandarkar, Senapati Bapat Marg, Law College etc.)
KNOWN_CANOPY_STREETS = {
    # Legendary FC Road tree cover
    "fergusson college road":        0.55,
    "fc road":                        0.55,
    "bhandarkar road":                0.50,
    "bhandarkar path":                0.50,
    # Senapati Bapat / Law College corridor
    "senapati bapat marg":           0.48,
    "law college road":               0.45,
    "prabhat road":                   0.42,
    # Karve Road corridor
    "karve road":                     0.35,
    "karve marg":                     0.35,
    # JM Road / University area
    "jangli maharaj road":            0.45,
    "jm road":                        0.45,
    # Tilak / Sambhaji / Deccan area
    "tilak road":                     0.38,
    "sambhaji bridge":                0.40,
    "chhatrapati sambhaji path":      0.42,
    # Gopal Ganesh Agarkar path
    "gopal ganesh agarkar path":      0.45,
    "agarkar path":                   0.45,
    # Vishnushastri Chiplunkar
    "vishnushastri chiplunkar path":  0.45,
    # Admiral Somnath path
    "admiral somnath path":           0.43,
    # Pune University campus roads
    "university road":                0.50,
}


def assign_canopy_bonus(gdf):
    """
    Assign tree_shade_bonus to every edge using heuristics.
    Returns updated GeoDataFrame.
    """
    df = gdf.copy()

    # Get shade fraction column for proxy (use 1300 = peak midday)
    shade_col = "shade_frac_1300"
    if shade_col not in df.columns:
        df[shade_col] = pd.to_numeric(df.get(shade_col, 0.15), errors="coerce").fillna(0.15)
    else:
        df[shade_col] = pd.to_numeric(df[shade_col], errors="coerce").fillna(0.15)

    # Clean street names for matching
    if "name" in df.columns:
        df["name_clean"] = df["name"].fillna("").str.lower().str.strip()
    else:
        df["name_clean"] = ""

    bonuses = []
    for _, row in df.iterrows():
        name_lower = str(row.get("name_clean", "")).lower()

        # 1. Name-based bonus
        name_bonus = 0.0
        for pattern, bonus in KNOWN_CANOPY_STREETS.items():
            if pattern in name_lower:
                name_bonus = bonus
                break

        # 2. Shade-fraction proxy: if existing shade >= 0.50, apply a 30% proxy bonus
        sf = float(row.get(shade_col, 0.15) or 0.15)
        shade_proxy = 0.0
        if sf >= 0.50:
            shade_proxy = round((sf - 0.50) * 0.6, 3)   # scales 0 to ~0.30

        # Combined bonus
        bonus = min(1.0, max(name_bonus, shade_proxy))
        bonuses.append(round(bonus, 4))

    df["tree_shade_bonus"] = bonuses
    df.drop(columns=["name_clean"], errors="ignore", inplace=True)

    # Print summary
    arr = np.array(bonuses)
    n_any  = (arr > 0).sum()
    n_high = (arr > 0.3).sum()
    print(f"\n-- Tree Shade Bonus Summary (Offline Heuristic) --")
    print(f"  Total edges            : {len(arr):,}")
    print(f"  Edges with any bonus   : {n_any:,}  ({n_any/len(arr)*100:.1f}%)")
    print(f"  Edges with >30% bonus  : {n_high:,}  ({n_high/len(arr)*100:.1f}%)")
    print(f"  Mean bonus             : {arr.mean()*100:.1f}%")
    print(f"  Max bonus              : {arr.max()*100:.1f}%")

    return df


def save_updated_gpkg(df):
    out_path = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
    df.to_file(out_path, driver="GPKG", layer="edges_shaded")
    print(f"\nUpdated GeoPackage written -> {out_path}")


def generate_canopy_map(df):
    bg      = "#0f0f23"
    panel   = "#111827"
    txt_col = "#e2e8f0"
    green   = "#10b981"
    amber   = "#f59e0b"
    grid_c  = "#1e2a3a"

    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.tick_params(colors=txt_col, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(grid_c)

    # Colour edges by tree_shade_bonus
    cmap = plt.cm.YlGn
    norm = plt.Normalize(vmin=0, vmax=0.6)

    df.plot(ax=ax, column="tree_shade_bonus",
            cmap=cmap, norm=norm, linewidth=0.9, alpha=0.88)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("Tree Canopy Shade Bonus (0 = no trees, 0.6 = dense canopy)",
                   color=txt_col, fontsize=9)
    cbar.ax.yaxis.set_tick_params(color=txt_col)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=txt_col)

    # Pilot bounding box
    west, south, east, north = BBOX
    rect = Rectangle((west, south), east - west, north - south,
                     linewidth=1.5, edgecolor=amber, facecolor="none",
                     linestyle="--", alpha=0.7)
    ax.add_patch(rect)

    # Annotate known green corridors
    known_labels = [
        (18.5262, 73.8419, "FC Road\n(55% canopy)"),
        (18.5165, 73.8268, "Law College Rd\n(45% canopy)"),
        (18.5085, 73.8342, "Karve Marg\n(35% canopy)"),
        (18.5192, 73.8471, "Sambhaji Bridge\n(40% canopy)"),
    ]
    for lat, lon, label in known_labels:
        ax.annotate(label, xy=(lon, lat),
                    fontsize=7, color="#a3e635",
                    ha="center", va="bottom",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="#0f2718",
                              edgecolor="#10b981", alpha=0.85))

    handles = [
        Patch(facecolor="#10b981", alpha=0.5, label="High canopy bonus (known corridors)"),
        Patch(facecolor="#f0c040", alpha=0.5, label="Moderate canopy proxy (shade fraction)"),
    ]
    ax.legend(handles=handles, fontsize=8,
              facecolor="#1a1a2e", labelcolor=txt_col, framealpha=0.85,
              loc="lower left")

    ax.set_title(
        "Day 7 · Tree Canopy Shade Bonus Map — Pune Pilot Area\n"
        "Heuristic model: known corridors + shadow-fraction proxy",
        fontsize=13, fontweight="bold", color=txt_col, pad=12
    )
    ax.set_xlabel("Longitude", color=txt_col)
    ax.set_ylabel("Latitude", color=txt_col)

    out_path = os.path.join(OUTPUTS_DIR, "day7_canopy_map.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=bg)
    plt.close()
    print(f"Saved canopy map -> {out_path}")
    return out_path


if __name__ == "__main__":
    print("=" * 60)
    print("  Pune Cooler Routes -- Day 7 Canopy Bonus (Offline)")
    print("=" * 60)

    shaded_path = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
    print(f"\nLoading {shaded_path}...")
    gdf = gpd.read_file(shaded_path)
    print(f"Loaded {len(gdf):,} edges.")

    updated = assign_canopy_bonus(gdf)
    save_updated_gpkg(updated)
    map_path = generate_canopy_map(updated)

    print("\n-- Day 7 Offline Canopy Complete --")
    print(f"  Map : {map_path}")
