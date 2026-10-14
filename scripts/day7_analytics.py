"""
day7_analytics.py
Day 7: Network-Wide Shade Analytics & Heat Index Visualization for Pune Cooler Routes.

This script:
1. Loads the full enriched road network (edges_shaded.gpkg).
2. Computes shade distribution statistics across ALL edges.
3. Generates a 4-panel analytics figure:
   - Panel A: Shade Fraction Distribution Histogram (0900 / 1300 / 1600)
   - Panel B: Top-20 Shadiest Corridors Bar Chart
   - Panel C: Midday Shade Tier Pie Chart with summary stats
   - Panel D: Sidewalk Quality vs Shade Scatter Analysis
4. Exports a shade-tier classification CSV for each edge.
5. Writes outputs/day7_analytics.png and outputs/day7_shade_tiers.csv
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
import osmnx as ox

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from config import DATA_PROCESSED_DIR, OUTPUTS_DIR, BBOX

# Shade tier thresholds (fraction of edge covered by shade)
TIER_DEEP     = 0.60   # >= 60% shade -> "Deep Canopy"
TIER_MODERATE = 0.35   # 35-60%       -> "Moderate Shade"
TIER_PARTIAL  = 0.15   # 15-35%       -> "Partial Shade"
# < 15%                               -> "Full Sun"


def classify_shade_tier(sf):
    """Return shade tier string for a given shade fraction (0 to 1)."""
    if sf >= TIER_DEEP:
        return "Deep Canopy"
    elif sf >= TIER_MODERATE:
        return "Moderate Shade"
    elif sf >= TIER_PARTIAL:
        return "Partial Shade"
    else:
        return "Full Sun"


def load_data():
    """Load the shaded edges GeoPackage and the base walking graph."""
    shaded_path  = os.path.join(DATA_PROCESSED_DIR, "edges_shaded.gpkg")
    graphml_path = os.path.join(DATA_PROCESSED_DIR, "network.graphml")

    print("Loading shaded edges GeoPackage...")
    gdf = gpd.read_file(shaded_path)

    print("Loading network GraphML...")
    G = ox.load_graphml(filepath=graphml_path)
    nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)

    return gdf, G, nodes_gdf, edges_gdf


def build_analytics_df(gdf):
    """Enrich edges GDF with shade tiers and sidewalk safety scores."""
    df = gdf.copy()

    # Coerce shade columns to float; fill missing values with sensible defaults
    for col, default in [("shade_frac_0900", 0.25),
                          ("shade_frac_1300", 0.15),
                          ("shade_frac_1600", 0.30)]:
        df[col] = pd.to_numeric(df.get(col, default), errors="coerce").fillna(default)

    # Weighted daily mean shade
    df["shade_daily_mean"] = (
        0.25 * df["shade_frac_0900"] +
        0.50 * df["shade_frac_1300"] +  # peak sun gets double weight
        0.25 * df["shade_frac_1600"]
    )

    # Shade tier at worst-case midday hour
    df["shade_tier_1300"] = df["shade_frac_1300"].apply(classify_shade_tier)

    # Sidewalk safety score: 1.0 = safe footway, 2.5 = risky arterial
    def sw_score(row):
        sw = str(row.get("sidewalk", "unknown")).lower()
        hw = str(row.get("highway", "residential")).lower()
        if sw in ("yes", "both", "left", "right", "separate") or "footway" in hw:
            return 1.0
        elif "residential" in hw or "living_street" in hw:
            return 1.5
        elif "primary" in hw or "secondary" in hw:
            return 2.5
        return 1.8

    df["sw_score"] = df.apply(sw_score, axis=1)

    # Clean length and name
    df["length"] = pd.to_numeric(df.get("length", 50.0), errors="coerce").fillna(50.0)
    df["name"]   = df.get("name", pd.Series(["Unnamed"] * len(df))).fillna("Unnamed Street")

    return df


def generate_analytics_figure(df):
    """Create and save the 4-panel dark-theme analytics figure."""
    # Dark theme colours
    bg       = "#0f0f23"
    panel_bg = "#111827"
    grid_col = "#1e2a3a"
    txt_col  = "#e2e8f0"
    cyan     = "#06b6d4"
    green    = "#10b981"
    amber    = "#f59e0b"
    red      = "#ef4444"

    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.patch.set_facecolor(bg)

    for ax in axes.flat:
        ax.set_facecolor(panel_bg)
        for spine in ax.spines.values():
            spine.set_edgecolor(grid_col)
        ax.tick_params(colors=txt_col, labelsize=9)
        ax.xaxis.label.set_color(txt_col)
        ax.yaxis.label.set_color(txt_col)
        ax.title.set_color(txt_col)

    # ── Panel A: Shade distribution histograms ──────────────────────────────
    ax = axes[0, 0]
    bins = np.linspace(0, 1, 25)
    slots = [
        ("shade_frac_0900", cyan,  "09:00 Morning Sun", 0.55),
        ("shade_frac_1300", amber, "13:00 Peak Midday", 0.75),
        ("shade_frac_1600", green, "16:00 Afternoon",   0.55),
    ]
    for col, color, label, alpha in slots:
        ax.hist(df[col].clip(0, 1), bins=bins, alpha=alpha,
                color=color, label=label, edgecolor="none")
    ax.axvline(0.35, color="#ffffff", linestyle="--", linewidth=1.2, alpha=0.6,
               label="35% comfort threshold")
    ax.set_title("A  ·  Shade Fraction Distribution Across All Edges",
                 fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Shade Fraction  (0 = Full Sun  →  1 = Full Shade)")
    ax.set_ylabel("Number of Road Edges")
    ax.legend(fontsize=8, facecolor="#1a1a2e", labelcolor=txt_col, framealpha=0.85)
    ax.grid(axis="y", color=grid_col, linewidth=0.5)

    # ── Panel B: Top-20 shadiest named corridors at 13:00 ──────────────────
    ax = axes[0, 1]
    named = df[df["name"] != "Unnamed Street"].copy()
    if len(named) > 0:
        agg = (
            named.groupby("name")
            .apply(lambda g: np.average(g["shade_frac_1300"], weights=g["length"]))
            .reset_index()
        )
        agg.columns = ["street", "shade1300"]
        top20 = agg.nlargest(20, "shade1300").sort_values("shade1300")
        bar_colors = [
            green if s >= TIER_DEEP else cyan if s >= TIER_MODERATE else amber
            for s in top20["shade1300"]
        ]
        bars = ax.barh(top20["street"], top20["shade1300"] * 100,
                       color=bar_colors, edgecolor="none", height=0.65)
        for bar, val in zip(bars, top20["shade1300"]):
            ax.text(bar.get_width() + 0.8,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val*100:.0f}%", va="center", color=txt_col, fontsize=8)
        ax.axvline(35, color="#ffffff", linestyle="--", linewidth=1, alpha=0.5)
        ax.set_xlim(0, 105)
    else:
        ax.text(0.5, 0.5, "No named streets found", transform=ax.transAxes,
                ha="center", va="center", color=txt_col)
    ax.set_title("B  ·  Top 20 Shadiest Corridors at Midday (13:00)",
                 fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Shade Coverage (%)")
    ax.tick_params(labelsize=7)
    ax.grid(axis="x", color=grid_col, linewidth=0.5)

    # ── Panel C: Shade tier pie chart ──────────────────────────────────────
    ax = axes[1, 0]
    tier_order  = ["Deep Canopy", "Moderate Shade", "Partial Shade", "Full Sun"]
    tier_colors = [green, cyan, amber, red]
    tier_counts = df["shade_tier_1300"].value_counts()
    sizes   = [tier_counts.get(t, 0) for t in tier_order]
    colors  = [c for t, c in zip(tier_order, tier_colors) if tier_counts.get(t, 0) > 0]
    labels  = [t for t in tier_order if tier_counts.get(t, 0) > 0]
    sizes_f = [s for s in sizes if s > 0]

    if sizes_f:
        wedges, texts, autotexts = ax.pie(
            sizes_f, labels=labels, colors=colors,
            autopct="%1.1f%%", startangle=90,
            pctdistance=0.78,
            wedgeprops=dict(edgecolor=bg, linewidth=2.5)
        )
        for t in texts + autotexts:
            t.set_color(txt_col)
            t.set_fontsize(9)

    total    = len(df)
    deep_n   = tier_counts.get("Deep Canopy", 0)
    sun_n    = tier_counts.get("Full Sun", 0)
    shade_n  = total - sun_n
    summary  = (
        f"Total edges : {total:,}\n"
        f"Deep canopy : {deep_n/total*100:.1f}%\n"
        f"Any shade   : {shade_n/total*100:.1f}%\n"
        f"Full sun    : {sun_n/total*100:.1f}%"
    )
    ax.text(1.30, 0, summary, transform=ax.transAxes, va="center",
            color=txt_col, fontsize=9,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#1e2a3a",
                      edgecolor=cyan, alpha=0.9))
    ax.set_title("C  ·  Midday Shade Tier Breakdown (All Edges)",
                 fontsize=12, fontweight="bold", pad=10)

    # ── Panel D: Sidewalk safety score vs midday shade scatter ─────────────
    ax = axes[1, 1]
    rng    = np.random.RandomState(42)
    jitter = rng.uniform(-0.04, 0.04, len(df))
    sc = ax.scatter(
        df["sw_score"] + jitter,
        df["shade_frac_1300"].clip(0, 1) * 100,
        c=df["shade_daily_mean"].clip(0, 1),
        cmap="YlGn", alpha=0.35, s=5, edgecolors="none"
    )
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label("Daily Mean Shade", color=txt_col, fontsize=9)
    cbar.ax.yaxis.set_tick_params(color=txt_col)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=txt_col)

    ax.axhline(35, color=amber, linestyle="--", linewidth=1.2, alpha=0.8,
               label="35% comfort threshold")
    ax.set_title("D  ·  Sidewalk Safety Score vs Midday Shade Coverage",
                 fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Sidewalk Safety Score  (1.0 = Safe Footway → 2.5 = Dangerous Arterial)")
    ax.set_ylabel("Midday Shade Coverage (%)")
    ax.set_xticks([1.0, 1.5, 1.8, 2.5])
    ax.set_xticklabels(["Safe\nFootway", "Residential", "Unknown", "Arterial\n(Risky)"],
                       fontsize=8)
    ax.legend(fontsize=8, facecolor="#1a1a2e", labelcolor=txt_col, framealpha=0.85)
    ax.grid(color=grid_col, linewidth=0.5, alpha=0.5)

    # ── Super title ─────────────────────────────────────────────────────────
    fig.suptitle(
        "Pune Cooler Routes  –  Day 7 Network-Wide Shade Analytics\n"
        "Pilot Area: Kothrud  ·  Karve Road  ·  Deccan Gymkhana  ·  FC Road",
        fontsize=15, fontweight="bold", color=txt_col, y=0.98
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    out_path = os.path.join(OUTPUTS_DIR, "day7_analytics.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved analytics figure -> {out_path}")
    return out_path


def export_shade_tiers(df):
    """Export per-edge shade tier classification CSV."""
    col_map = {
        "u":              "from_node",
        "v":              "to_node",
        "name":           "street_name",
        "highway":        "road_type",
        "length":         "length_m",
        "shade_frac_0900":"shade_0900",
        "shade_frac_1300":"shade_1300",
        "shade_frac_1600":"shade_1600",
        "shade_daily_mean":"shade_daily_mean",
        "shade_tier_1300":"shade_tier_midday",
        "sw_score":       "sidewalk_safety_score",
    }
    available = {k: v for k, v in col_map.items() if k in df.columns}
    out = df[list(available.keys())].rename(columns=available).copy()

    for c in ["shade_0900", "shade_1300", "shade_1600", "shade_daily_mean", "sidewalk_safety_score"]:
        if c in out.columns:
            out[c] = out[c].round(4)

    out_path = os.path.join(OUTPUTS_DIR, "day7_shade_tiers.csv")
    out.to_csv(out_path, index=False)
    print(f"Saved shade tier CSV -> {out_path}  ({len(out):,} edges)")

    print("\n-- Shade Tier Summary (Midday 13:00) --")
    for tier in ["Deep Canopy", "Moderate Shade", "Partial Shade", "Full Sun"]:
        n   = (out["shade_tier_midday"] == tier).sum()
        pct = n / len(out) * 100
        print(f"  {tier:<20}: {n:>5} edges  ({pct:.1f}%)")
    print(f"  {'TOTAL':<20}: {len(out):>5} edges\n")

    return out_path


def print_top_corridors(df, n=10):
    """Print table of top N shadiest named streets."""
    named = df[df["name"] != "Unnamed Street"].copy()
    if len(named) == 0:
        print("No named streets found.")
        return

    summary = (
        named.groupby("name")
        .apply(lambda g: pd.Series({
            "total_length_m": g["length"].sum(),
            "shade_0900": np.average(g["shade_frac_0900"], weights=g["length"]),
            "shade_1300": np.average(g["shade_frac_1300"], weights=g["length"]),
            "shade_1600": np.average(g["shade_frac_1600"], weights=g["length"]),
        }))
        .reset_index()
        .sort_values("shade_1300", ascending=False)
        .head(n)
    )

    print(f"\n-- Top {n} Shadiest Walking Corridors (weighted by edge length) --")
    print(f"  {'Street Name':<35} {'09:00':>6} {'13:00':>6} {'16:00':>6}  {'Length':>8}")
    print("  " + "-" * 68)
    for _, row in summary.iterrows():
        print(f"  {str(row['name'])[:34]:<35} "
              f"{row['shade_0900']*100:>5.1f}% "
              f"{row['shade_1300']*100:>5.1f}% "
              f"{row['shade_1600']*100:>5.1f}%  "
              f"{row['total_length_m']:>7.0f} m")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("  Pune Cooler Routes -- Day 7 Network Analytics")
    print("=" * 60)

    gdf, G, nodes_gdf, edges_gdf = load_data()
    df = build_analytics_df(gdf)
    print(f"\nLoaded {len(df):,} edges for analysis.\n")

    print_top_corridors(df, n=10)
    fig_path = generate_analytics_figure(df)
    csv_path = export_shade_tiers(df)

    print("-- Day 7 Analytics Complete --")
    print(f"  Figure : {fig_path}")
    print(f"  CSV    : {csv_path}")
