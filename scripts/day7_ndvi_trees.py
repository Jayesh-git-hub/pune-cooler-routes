"""
day7_ndvi_trees.py
Day 7: Green Canopy Integration for Pune Cooler Routes.

Addresses Loophole #1: "The Missing Trees Problem" from the Day 1 analysis.
In Pune (FC Road, Bhandarkar Road, university campuses), old canopy trees
provide the majority of pedestrian shade that building footprints alone miss.

Pipeline:
  1. Download OSM green-space features (parks + natural areas combined) with timeout.
  2. Buffer any point features by 8 m (tree crown approximation).
  3. Union all green polygons into a single GreenCanopy geometry (metric CRS).
  4. For each road edge compute:
       tree_shade_bonus = overlap_length / edge_length  (0..1)
  5. Update edges_shaded.gpkg with the new column.
  6. Generate outputs/day7_canopy_map.png.

The download is wrapped in a try/except with a short timeout so the script
never hangs indefinitely. If OSM data cannot be fetched, a graceful fallback
skips the bonus computation and still produces the map.
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box
from shapely.ops import unary_union
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import osmnx as ox

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from config import DATA_PROCESSED_DIR, OUTPUTS_DIR, BBOX

TREE_CROWN_RADIUS_M = 8.0   # metres radius assumed per point-tree feature
METRIC_CRS          = "EPSG:32643"   # UTM Zone 43N (covers Pune)
OSM_TIMEOUT         = 60    # seconds to wait for each Overpass request


def _fetch_one_tag(bbox_tuple, tags, label):
    """
    Try a single OSMnx features download with error handling.
    Returns a GeoDataFrame or None on failure.
    """
    north, south, east, west = bbox_tuple
    try:
        gdf = ox.features_from_bbox(
            bbox=(north, south, east, west),
            tags=tags
        )
        print(f"  {label}: {len(gdf)} features downloaded")
        return gdf[["geometry"]].copy()
    except Exception as e:
        print(f"  {label}: skipped ({type(e).__name__}: {str(e)[:80]})")
        return None


def download_green_infrastructure():
    """
    Download OSM green-space polygons inside the pilot bounding box.
    Uses two broad tag queries and buffers point trees.
    Returns combined GeoDataFrame in WGS84.
    """
    west, south, east, north = BBOX
    bbox_tuple = (north, south, east, west)

    # Configure osmnx timeout
    ox.settings.timeout = OSM_TIMEOUT

    print("Downloading OSM green infrastructure (timeout=60s per query)...")
    gdfs = []

    # Query 1: leisure parks / gardens
    r = _fetch_one_tag(bbox_tuple,
                       {"leisure": ["park", "garden", "nature_reserve"]},
                       "Parks / gardens")
    if r is not None:
        gdfs.append(r)

    # Query 2: natural features (wood, scrub, grassland, tree_row)
    r = _fetch_one_tag(bbox_tuple,
                       {"natural": ["wood", "scrub", "grassland", "tree_row", "tree"]},
                       "Natural features")
    if r is not None:
        # Buffer point trees in metric CRS
        r_m = r.to_crs(METRIC_CRS)
        r_m["geometry"] = r_m["geometry"].apply(
            lambda g: g.buffer(TREE_CROWN_RADIUS_M) if g.geom_type == "Point" else g
        )
        gdfs.append(r_m.to_crs("EPSG:4326")[["geometry"]].copy())

    if not gdfs:
        print("  WARNING: No green features could be downloaded. Proceeding with empty canopy.")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    combined = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs="EPSG:4326")
    combined = combined[combined.geometry.notna()].copy()
    # Keep polygon-like geometries only
    combined = combined[combined.geometry.geom_type.isin(
        ["Polygon", "MultiPolygon"]
    )].copy()
    print(f"  Total usable green polygons: {len(combined)}")
    return combined


def build_canopy_union(green_gdf):
    """Union all green polygons -> single Shapely geometry in METRIC_CRS."""
    if len(green_gdf) == 0:
        empty_poly = box(0, 0, 0, 0)
        return empty_poly, 0.0

    green_m   = green_gdf.to_crs(METRIC_CRS)
    canopy    = unary_union(green_m.geometry.values)
    area_km2  = canopy.area / 1e6
    print(f"  Green canopy union area: {area_km2:.3f} km^2")
    return canopy, area_km2


def compute_tree_shade_bonus(shaded_gdf, canopy_union):
    """
    Compute tree_shade_bonus for every edge:
        bonus = overlap_length / edge_length  (clamped to [0, 1])
    Edges that don't touch any canopy get bonus = 0.0.
    """
    print(f"Computing tree shade bonus for {len(shaded_gdf):,} edges...")
    edges_m  = shaded_gdf.copy().to_crs(METRIC_CRS)
    bonuses  = []

    # Bail early if canopy is empty or degenerate
    canopy_empty = (canopy_union is None or
                    (hasattr(canopy_union, "is_empty") and canopy_union.is_empty) or
                    (hasattr(canopy_union, "area") and canopy_union.area < 1.0))

    for _, row in edges_m.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty or canopy_empty:
            bonuses.append(0.0)
            continue
        try:
            overlap     = geom.intersection(canopy_union)
            overlap_len = overlap.length if not overlap.is_empty else 0.0
            edge_len    = geom.length
            bonus = min(1.0, overlap_len / edge_len) if edge_len > 0 else 0.0
        except Exception:
            bonus = 0.0
        bonuses.append(round(bonus, 4))

    edges_m["tree_shade_bonus"] = bonuses
    result = edges_m.to_crs("EPSG:4326")

    # Summary
    arr = np.array(bonuses)
    n_any  = (arr > 0).sum()
    n_high = (arr > 0.3).sum()
    print(f"  Edges with any canopy bonus  : {n_any:,} ({n_any/len(arr)*100:.1f}%)")
    print(f"  Edges with >30% canopy bonus : {n_high:,} ({n_high/len(arr)*100:.1f}%)")
    print(f"  Mean bonus                   : {arr.mean()*100:.1f}%")
    return result


def update_edges_gpkg(updated_gdf):
    """Write tree_shade_bonus back to edges_shaded.gpkg."""
    gpkg_path = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
    print(f"Writing updated GeoPackage -> {gpkg_path}")
    updated_gdf.to_file(gpkg_path, driver="GPKG", layer="edges_shaded")
    print("  Done.")


def generate_canopy_map(green_gdf, edges_gdf):
    """
    Save a dark-theme map coloring the road network by tree_shade_bonus.
    """
    bg      = "#0f0f23"
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

    # Draw green canopy polygons (if any)
    if len(green_gdf) > 0:
        green_gdf.plot(ax=ax, color=green, alpha=0.22, edgecolor="none")

    # Draw road edges coloured by bonus
    has_bonus = ("tree_shade_bonus" in edges_gdf.columns and
                 edges_gdf["tree_shade_bonus"].max() > 0)
    if has_bonus:
        cmap = plt.cm.YlGn
        norm = plt.Normalize(vmin=0, vmax=1)
        edges_gdf.plot(ax=ax, column="tree_shade_bonus",
                       cmap=cmap, norm=norm, linewidth=0.8, alpha=0.85)
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
        cbar.set_label("Tree Shade Bonus (0=no canopy, 1=full canopy)",
                       color=txt_col, fontsize=9)
        cbar.ax.yaxis.set_tick_params(color=txt_col)
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color=txt_col)
    else:
        # No bonus data — draw edges in neutral colour
        edges_gdf.plot(ax=ax, color="#334155", linewidth=0.6, alpha=0.7)
        ax.text(0.5, 0.97,
                "Note: OSM canopy data unavailable – edges shown without bonus",
                transform=ax.transAxes, ha="center", va="top",
                color=amber, fontsize=9)

    # Pilot bounding box
    from matplotlib.patches import Rectangle
    west, south, east, north = BBOX
    rect = Rectangle((west, south), east - west, north - south,
                     linewidth=1.5, edgecolor=amber, facecolor="none",
                     linestyle="--", alpha=0.7)
    ax.add_patch(rect)

    # Legend patch for green polygons
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=green, alpha=0.4, label="OSM Green Space (parks/forests)")]
    ax.legend(handles=handles, fontsize=8,
              facecolor="#1a1a2e", labelcolor=txt_col, framealpha=0.85)

    ax.set_title(
        "Day 7 · OSM Tree Canopy Coverage Map\n"
        "Road network coloured by green-infrastructure shade bonus",
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
    print("  Pune Cooler Routes -- Day 7 Tree Canopy Integration")
    print("=" * 60)

    # Load existing shaded edges
    shaded_path = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
    print(f"\nLoading {shaded_path}...")
    shaded_gdf = gpd.read_file(shaded_path)
    print(f"Loaded {len(shaded_gdf):,} edges.\n")

    # Download green infrastructure (with timeout protection)
    green_gdf = download_green_infrastructure()

    # Build canopy union geometry
    canopy_union, canopy_area_km2 = build_canopy_union(green_gdf)

    # Compute per-edge shade bonus
    updated_gdf = compute_tree_shade_bonus(shaded_gdf, canopy_union)

    # Write updated GeoPackage
    update_edges_gpkg(updated_gdf)

    # Generate canopy map
    map_path = generate_canopy_map(green_gdf, updated_gdf)

    print("\n-- Day 7 Tree Canopy Integration Complete --")
    print(f"  Green canopy area : {canopy_area_km2:.3f} km^2")
    print(f"  Canopy map        : {map_path}")
    print("--------------------------------------------\n")
