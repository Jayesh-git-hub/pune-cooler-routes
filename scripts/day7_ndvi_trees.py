"""
day7_ndvi_trees.py
Day 7: NDVI / Green Canopy Integration for Pune Cooler Routes.

Addresses the "Missing Trees" loophole identified on Day 1:
  In Pune (FC Road, Bhandarkar Road, university campuses), massive old canopy
  trees provide the majority of pedestrian shade. This script fetches OSM
  vegetation features (parks, trees, forests, natural areas) and computes a
  tree-canopy shade BONUS for each road edge.

Pipeline:
1. Download OSM green infrastructure (parks, natural, landuse=forest/grass, trees)
   within the pilot bounding box.
2. Buffer point trees by 8 m radius (crown spread approximation).
3. Union all green polygons into a single GreenCanopy geometry.
4. For each road edge:
   a. Compute overlap length between edge and green canopy.
   b. Compute tree_shade_bonus = overlap_length / edge_length  (0 to 1)
5. Update edges_shaded.gpkg: write tree_shade_bonus column.
6. Print canopy coverage summary and save outputs/day7_canopy_map.png.
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

# Tree crown radius assumption (metres) for OSM point trees
TREE_CROWN_RADIUS_M = 8.0

# CRS for metric calculations (UTM Zone 43N covers Pune)
METRIC_CRS = "EPSG:32643"


def download_green_infrastructure():
    """
    Download OSM green space features (parks, forests, trees, grass, natural)
    within the pilot bounding box. Returns a GeoDataFrame in WGS84.
    """
    west, south, east, north = BBOX
    print("Downloading OSM green infrastructure...")

    gdfs = []

    # 1. Parks and public gardens
    try:
        parks = ox.features_from_bbox(
            bbox=(north, south, east, west),
            tags={"leisure": ["park", "garden", "nature_reserve"]}
        )
        gdfs.append(parks[["geometry"]].copy())
        print(f"  Parks / gardens: {len(parks)} features")
    except Exception as e:
        print(f"  Parks download skipped: {e}")

    # 2. Forests, grass, scrub, meadow (landuse)
    try:
        landuse = ox.features_from_bbox(
            bbox=(north, south, east, west),
            tags={"landuse": ["forest", "grass", "meadow", "farmland"]}
        )
        gdfs.append(landuse[["geometry"]].copy())
        print(f"  Landuse green: {len(landuse)} features")
    except Exception as e:
        print(f"  Landuse download skipped: {e}")

    # 3. Natural features (wood, scrub, grassland)
    try:
        natural = ox.features_from_bbox(
            bbox=(north, south, east, west),
            tags={"natural": ["wood", "scrub", "grassland", "tree_row"]}
        )
        gdfs.append(natural[["geometry"]].copy())
        print(f"  Natural features: {len(natural)} features")
    except Exception as e:
        print(f"  Natural features download skipped: {e}")

    # 4. Individual trees (points) - buffer by crown radius
    try:
        trees = ox.features_from_bbox(
            bbox=(north, south, east, west),
            tags={"natural": "tree"}
        )
        print(f"  Individual trees (points): {len(trees)} features")
        # Project to metric CRS for buffering
        trees_m = trees[["geometry"]].copy().to_crs(METRIC_CRS)
        # Buffer only Point geometries by crown radius
        trees_m["geometry"] = trees_m["geometry"].apply(
            lambda g: g.buffer(TREE_CROWN_RADIUS_M) if g.geom_type == "Point" else g
        )
        trees_wgs = trees_m.to_crs("EPSG:4326")
        gdfs.append(trees_wgs[["geometry"]].copy())
    except Exception as e:
        print(f"  Individual trees download skipped: {e}")

    if not gdfs:
        print("WARNING: No green infrastructure data downloaded. Using empty canopy.")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    combined = gpd.GeoDataFrame(
        pd.concat(gdfs, ignore_index=True),
        crs="EPSG:4326"
    )
    # Keep only valid polygon/multipolygon geometries
    combined = combined[combined.geometry.notna()].copy()
    combined = combined[combined.geometry.geom_type.isin(
        ["Polygon", "MultiPolygon"]
    )].copy()

    print(f"  Total green features (polygons only): {len(combined)}")
    return combined


def build_canopy_union(green_gdf):
    """
    Union all green features into a single GreenCanopy geometry (metric CRS).
    """
    if len(green_gdf) == 0:
        # Return empty polygon in metric CRS
        return gpd.GeoSeries([box(0, 0, 0, 0)], crs=METRIC_CRS)[0]

    green_m = green_gdf.to_crs(METRIC_CRS)
    canopy_union = unary_union(green_m.geometry.values)
    print(f"  Green canopy union area: {canopy_union.area / 1e6:.3f} km^2")
    return canopy_union  # Shapely geometry in METRIC_CRS


def compute_tree_shade_bonus(shaded_gdf, canopy_union):
    """
    For each road edge, compute tree_shade_bonus = (overlap with canopy) / edge_length.
    Returns updated GeoDataFrame with new 'tree_shade_bonus' column.
    """
    print("Computing tree shade bonus per edge...")

    # Project edges to metric CRS
    edges_m = shaded_gdf.copy().to_crs(METRIC_CRS)

    bonuses = []
    for idx, row in edges_m.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            bonuses.append(0.0)
            continue

        try:
            overlap  = geom.intersection(canopy_union)
            overlap_len = overlap.length if not overlap.is_empty else 0.0
            edge_len    = geom.length
            bonus = min(1.0, overlap_len / edge_len) if edge_len > 0 else 0.0
        except Exception:
            bonus = 0.0

        bonuses.append(round(bonus, 4))

    edges_m["tree_shade_bonus"] = bonuses

    # Convert back to WGS84
    result = edges_m.to_crs("EPSG:4326")
    return result


def update_edges_gpkg(updated_gdf):
    """Write updated tree_shade_bonus column back into edges_shaded.gpkg."""
    gpkg_path = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
    updated_gdf.to_file(gpkg_path, driver="GPKG", layer="edges_shaded")
    print(f"Updated edges_shaded.gpkg with tree_shade_bonus -> {gpkg_path}")


def generate_canopy_map(green_gdf, shaded_with_bonus):
    """
    Save a map showing: pilot area road network coloured by tree_shade_bonus.
    """
    bg      = "#0f0f23"
    txt_col = "#e2e8f0"
    green   = "#10b981"
    amber   = "#f59e0b"

    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.tick_params(colors=txt_col, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#1e2a3a")

    # Draw green canopy polygons
    if len(green_gdf) > 0:
        green_gdf.plot(ax=ax, color=green, alpha=0.25, edgecolor="none")

    # Draw road edges coloured by tree_shade_bonus
    if "tree_shade_bonus" in shaded_with_bonus.columns:
        cmap = plt.cm.YlGn
        norm = plt.Normalize(vmin=0, vmax=1)
        shaded_with_bonus.plot(
            ax=ax,
            column="tree_shade_bonus",
            cmap=cmap,
            norm=norm,
            linewidth=0.8,
            alpha=0.85
        )
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.03, pad=0.04)
        cbar.set_label("Tree Shade Bonus (0 = no trees, 1 = full canopy)",
                       color=txt_col, fontsize=9)
        cbar.ax.yaxis.set_tick_params(color=txt_col)
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color=txt_col)

    # Pilot bounding box
    west, south, east, north = BBOX
    from matplotlib.patches import Rectangle
    rect = Rectangle((west, south), east - west, north - south,
                     linewidth=1.5, edgecolor=amber, facecolor="none",
                     linestyle="--", alpha=0.7)
    ax.add_patch(rect)

    ax.set_title(
        "Day 7 · Tree Canopy Coverage Map\n"
        "Road network coloured by OSM green-infrastructure shade bonus",
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


def print_canopy_summary(shaded_gdf):
    """Print a summary of tree shade bonus statistics."""
    col = "tree_shade_bonus"
    if col not in shaded_gdf.columns:
        print("No tree_shade_bonus column found.")
        return

    vals = shaded_gdf[col].values
    total = len(vals)

    print("\n-- Tree Canopy Shade Bonus Summary --")
    print(f"  Total edges analysed : {total:,}")
    print(f"  Mean bonus           : {vals.mean()*100:.1f}%")
    print(f"  Max bonus            : {vals.max()*100:.1f}%")
    print(f"  Edges with >0% bonus : {(vals > 0).sum():,}  ({(vals > 0).sum()/total*100:.1f}%)")
    print(f"  Edges with >30% bonus: {(vals > 0.3).sum():,}  ({(vals > 0.3).sum()/total*100:.1f}%)")
    print(f"  Edges with >60% bonus: {(vals > 0.6).sum():,}  ({(vals > 0.6).sum()/total*100:.1f}%)")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("  Pune Cooler Routes -- Day 7 Tree Canopy Integration")
    print("=" * 60)

    # Load existing shaded edges
    shaded_path = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
    print(f"\nLoading {shaded_path}...")
    shaded_gdf = gpd.read_file(shaded_path)
    print(f"Loaded {len(shaded_gdf):,} edges.\n")

    # Download and union green infrastructure
    green_gdf    = download_green_infrastructure()
    canopy_union = build_canopy_union(green_gdf)

    # Compute tree shade bonus per edge
    updated_gdf  = compute_tree_shade_bonus(shaded_gdf, canopy_union)

    # Print summary statistics
    print_canopy_summary(updated_gdf)

    # Save updated GeoPackage
    update_edges_gpkg(updated_gdf)

    # Generate canopy map
    map_path = generate_canopy_map(green_gdf, updated_gdf)

    print("-- Day 7 Tree Canopy Integration Complete --")
    print(f"  Canopy Map : {map_path}")
