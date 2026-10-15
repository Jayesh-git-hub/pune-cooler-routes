"""
day9_report_generator.py
Day 9: Comprehensive HTML Report Generator for Pune Cooler Routes.

Generates a polished, self-contained HTML report embedding:
  - All analytics figures (Day 7 & Day 8 charts as embedded base64 PNGs)
  - 7-day sprint summary
  - Neighbourhood shade score table
  - Benchmark results table
  - Routing stats (top corridors)
  - Project architecture
  - Smart waypoint recommendations (if CSV exists)

Output:
  - outputs/day9_full_report.html  (fully self-contained, shareable HTML file)
"""
import os, sys, json, base64, datetime, warnings
warnings.filterwarnings("ignore")

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from config import OUTPUTS_DIR

def embed_image(path, max_height=500):
    """Embed image as base64 data URI."""
    if not os.path.exists(path):
        return f'<p class="img-missing">Image not available: {os.path.basename(path)}</p>'
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/png")
    return f'<img src="data:{mime};base64,{data}" style="max-width:100%;max-height:{max_height}px;border-radius:12px;margin:8px 0;" />'


def df_to_html(df, row_classes=None):
    """Convert DataFrame to styled HTML table."""
    html = '<table class="data-table"><thead><tr>'
    for col in df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for i, (_, row) in enumerate(df.iterrows()):
        rc = row_classes[i] if row_classes and i < len(row_classes) else ""
        html += f'<tr class="{rc}">'
        for val in row.values:
            html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


def build_report():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Load data
    nb_csv  = os.path.join(OUTPUTS_DIR, "day8_neighbourhood_scores.csv")
    bm_csv  = os.path.join(OUTPUTS_DIR, "day6_benchmark_25routes.csv")
    wp_csv  = os.path.join(OUTPUTS_DIR, "day9_waypoint_recommendations.csv")
    tier_csv = os.path.join(OUTPUTS_DIR, "day7_shade_tiers.csv")

    nb_df = pd.read_csv(nb_csv)[["neighbourhood","edges_count","shade_frac_1300","composite_shade"]] if os.path.exists(nb_csv) else pd.DataFrame()
    bm_df = pd.read_csv(bm_csv).head(10) if os.path.exists(bm_csv) else pd.DataFrame()
    wp_df = pd.read_csv(wp_csv).head(5) if os.path.exists(wp_csv) else pd.DataFrame()

    # Sprint milestones
    sprint = [
        ("Day 1", "Network Download & Sidewalk Audit", "3,971 nodes · 10,414 edges · OSM walking network"),
        ("Day 2", "Building Footprints & Height Modeling", "OSM building dataset with estimated heights"),
        ("Day 3", "Solar Shadow Simulation (pybdshadow)", "edges_shaded.gpkg: shade fracs at 09:00 / 13:00 / 16:00"),
        ("Day 4", "Dual Routing Engine v1", "Fastest vs Coolest route with Dijkstra on shade-weighted graph"),
        ("Day 5", "Full-Stack Interactive Web App", "Live Leaflet map · REST API · Turn-by-turn steps"),
        ("Day 6", "Multi-Criteria Thermal Comfort Router", "Shade + Sidewalk + Safety · 25-route benchmark · −3.2°C relief"),
        ("Day 7", "Tree Canopy Integration & Analytics", "OSM green canopy bonus · 10,414-edge shade tier classification"),
        ("Day 8", "Shade Heatmap & Isochrone Analysis", "3-panel heatmap · Composite score map · 5/10/15-min isochrones"),
        ("Day 9", "Smart Waypoint Planner & Full Report", "Best intermediate shade waypoints · Comprehensive HTML report"),
    ]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pune Cooler Routes — Full 9-Day Sprint Report</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0f0f23; --bg2: #1a1a35; --bg3: #1e2a3a;
    --text: #e2e8f0; --text2: #94a3b8; --text3: #64748b;
    --green: #10b981; --amber: #f59e0b; --blue: #38bdf8; --purple: #a78bfa; --red: #ef4444;
    --border: rgba(255,255,255,0.06); --glow: rgba(16,185,129,0.15);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; line-height: 1.6; }}
  .hero {{ background: linear-gradient(135deg, #0f0f23 0%, #1a1a35 50%, #0f2640 100%);
            padding: 80px 40px; text-align: center; border-bottom: 1px solid var(--border); }}
  .hero h1 {{ font-family: 'Outfit', sans-serif; font-size: 3rem; font-weight: 800;
               background: linear-gradient(90deg, var(--green), var(--blue));
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  .hero .sub {{ font-size: 1.2rem; color: var(--text2); margin-top: 12px; }}
  .hero .meta {{ display:flex; justify-content:center; gap:24px; margin-top:28px; flex-wrap:wrap; }}
  .hero .badge {{ background: var(--bg3); border: 1px solid var(--border); border-radius: 20px;
                  padding: 6px 18px; font-size: 0.85rem; color: var(--text2); }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 24px; }}
  h2 {{ font-family: 'Outfit', sans-serif; font-size: 1.8rem; color: var(--green);
        margin: 48px 0 20px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }}
  h3 {{ font-size: 1.1rem; color: var(--blue); margin: 28px 0 12px; font-weight: 600; }}
  p {{ color: var(--text2); margin-bottom: 12px; }}
  .sprint-table {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; margin-top: 20px; }}
  .sprint-card {{ background: var(--bg2); border: 1px solid var(--border); border-radius: 12px;
                  padding: 18px; transition: border-color .2s; }}
  .sprint-card:hover {{ border-color: var(--green); }}
  .sprint-card .day-badge {{ display: inline-block; background: var(--green); color: #0f0f23;
                              border-radius: 6px; padding: 2px 10px; font-size: 0.75rem; font-weight: 700; margin-bottom: 8px; }}
  .sprint-card h4 {{ font-size: 0.95rem; color: var(--text); margin-bottom: 6px; }}
  .sprint-card p {{ font-size: 0.82rem; color: var(--text3); margin: 0; }}
  .data-table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.88rem; }}
  .data-table th {{ background: var(--bg3); color: var(--blue); text-align: left; padding: 10px 14px;
                    font-weight: 600; border-bottom: 1px solid var(--border); }}
  .data-table td {{ padding: 9px 14px; border-bottom: 1px solid var(--border); color: var(--text2); }}
  .data-table tr:hover td {{ background: var(--bg2); color: var(--text); }}
  .img-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }}
  .img-grid.single {{ grid-template-columns: 1fr; }}
  .img-box {{ background: var(--bg2); border: 1px solid var(--border); border-radius: 12px;
               padding: 16px; text-align: center; }}
  .img-box h4 {{ color: var(--text2); font-size: 0.85rem; margin-bottom: 10px; font-weight: 500; }}
  .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; margin: 20px 0; }}
  .stat-card {{ background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center; }}
  .stat-card .val {{ font-family: 'Outfit', sans-serif; font-size: 2rem; font-weight: 700; color: var(--green); }}
  .stat-card .lbl {{ font-size: 0.8rem; color: var(--text3); margin-top: 4px; }}
  .highlight {{ color: var(--amber); }}
  .img-missing {{ color: var(--text3); font-style: italic; padding: 12px; text-align: center; }}
  .footer {{ text-align: center; padding: 40px; color: var(--text3); border-top: 1px solid var(--border); margin-top: 60px; }}
  @media(max-width: 700px) {{ .img-grid {{ grid-template-columns: 1fr; }} .hero h1 {{ font-size: 2rem; }} }}
</style>
</head>
<body>

<div class="hero">
  <h1>🌿 Pune Cooler Routes</h1>
  <p class="sub">Full 9-Day Research Sprint Report · Shade-Aware Pedestrian Navigation · Pune, India</p>
  <div class="meta">
    <span class="badge">📅 Generated: {now}</span>
    <span class="badge">🗺️ Pilot Area: Kothrud → FC Road</span>
    <span class="badge">🔢 10,414 Edges Analysed</span>
    <span class="badge">🌡️ −3.2°C Thermal Relief</span>
  </div>
</div>

<div class="container">

  <h2>9-Day Sprint Summary</h2>
  <p>A complete walk-optimization system built in 9 days using OpenStreetMap data, solar shadow simulation, and multi-criteria routing algorithms.</p>
  <div class="sprint-table">
"""
    for day, title, desc in sprint:
        html += f"""
    <div class="sprint-card">
      <span class="day-badge">{day}</span>
      <h4>{title}</h4>
      <p>{desc}</p>
    </div>"""

    html += """
  </div>

  <h2>Key Results</h2>
  <div class="stat-grid">
    <div class="stat-card"><div class="val">3,971</div><div class="lbl">Network Nodes</div></div>
    <div class="stat-card"><div class="val">10,414</div><div class="lbl">Road Edges Analysed</div></div>
    <div class="stat-card"><div class="val">3</div><div class="lbl">Shadow Time Slots (09:00/13:00/16:00)</div></div>
    <div class="stat-card"><div class="val">3</div><div class="lbl">Routing Engines (Fastest/Coolest/Balanced)</div></div>
    <div class="stat-card"><div class="val" style="color:var(--amber)">−3.2°C</div><div class="lbl">Apparent Temperature Relief (Coolest Route)</div></div>
    <div class="stat-card"><div class="val">+4.2%</div><div class="lbl">Extra Shade at Only +44.6m Extra Walk</div></div>
    <div class="stat-card"><div class="val">56.1%</div><div class="lbl">Senapati Bapat Marg Midday Shade</div></div>
    <div class="stat-card"><div class="val">3.21 MB</div><div class="lbl">Shade Heatmap GeoJSON (10,414 edges)</div></div>
  </div>

  <h2>Day 8 · Shade Heatmap</h2>
  <p>3-panel choropleth map of shade fraction across the pilot network at each time of day.</p>
"""
    html += '<div class="img-grid single"><div class="img-box"><h4>3-Panel Time-of-Day Shade Heatmap</h4>'
    html += embed_image(os.path.join(OUTPUTS_DIR, "day8_shade_heatmap.png"), max_height=500)
    html += '</div></div>'

    html += '<div class="img-grid single"><div class="img-box"><h4>Composite Shade Score Map (Weighted Average: 25% Morning + 50% Midday + 25% Afternoon + 15% Tree Canopy)</h4>'
    html += embed_image(os.path.join(OUTPUTS_DIR, "day8_composite_shade.png"), max_height=500)
    html += '</div></div>'

    if not nb_df.empty:
        html += "<h3>Neighbourhood Shade League Table</h3>"
        nb_df.columns = ["Neighbourhood", "Edges", "Midday Shade", "Composite Score"]
        nb_df["Midday Shade"] = nb_df["Midday Shade"].map(lambda x: f"{x*100:.1f}%")
        nb_df["Composite Score"] = nb_df["Composite Score"].map(lambda x: f"{x*100:.1f}%")
        html += df_to_html(nb_df)

    html += """
  <h2>Day 8 · Isochrone Analysis</h2>
  <p>Walking reachability contours (5 / 10 / 15 minutes) from Deccan Gymkhana comparing standard vs shade-priority walking.</p>
"""
    html += '<div class="img-grid single"><div class="img-box"><h4>Standard Walk vs Shade-Priority Isochrones (5 / 10 / 15 min)</h4>'
    html += embed_image(os.path.join(OUTPUTS_DIR, "day8_isochrone_comparison.png"), max_height=500)
    html += "</div></div>"

    html += """
  <h2>Day 7 · Network Analytics</h2>
"""
    html += '<div class="img-grid single"><div class="img-box"><h4>4-Panel Shade Analytics Dashboard (10,414 Edges)</h4>'
    html += embed_image(os.path.join(OUTPUTS_DIR, "day7_analytics.png"), max_height=480)
    html += "</div></div>"

    html += '<div class="img-grid"><div class="img-box"><h4>Tree Canopy Coverage Map</h4>'
    html += embed_image(os.path.join(OUTPUTS_DIR, "day7_canopy_map.png"), max_height=380)
    html += '</div><div class="img-box"><h4>Day 6 Benchmark: 25 Route Pairs</h4>'
    html += embed_image(os.path.join(OUTPUTS_DIR, "day6_benchmark.png"), max_height=380)
    html += "</div></div>"

    if not bm_df.empty:
        html += "<h3>Day 6 Benchmark Results (Sample: Top 10 Routes)</h3>"
        html += df_to_html(bm_df)

    html += """
  <h2>Day 9 · Smart Waypoint Planner</h2>
  <p>Best intermediate shade waypoints between MIT-WPU and Fergusson College, ranked by shade gain per detour metre.</p>
"""
    html += '<div class="img-grid single"><div class="img-box"><h4>Top-3 Shade-Boosted Waypoint Routes vs Direct Coolest</h4>'
    html += embed_image(os.path.join(OUTPUTS_DIR, "day9_smart_planner.png"), max_height=480)
    html += "</div></div>"

    if not wp_df.empty:
        html += "<h3>Top Waypoint Recommendations</h3>"
        html += df_to_html(wp_df)

    html += """
  <h2>Tech Stack</h2>
  <div class="sprint-table">
    <div class="sprint-card"><h4>🗺️ OSMnx + NetworkX</h4><p>Walking graph download, Dijkstra shortest paths, node snapping</p></div>
    <div class="sprint-card"><h4>🌞 pybdshadow</h4><p>3D building shadow simulation at 09:00 / 13:00 / 16:00 solar angles</p></div>
    <div class="sprint-card"><h4>📐 GeoPandas + Shapely</h4><p>Geospatial edge operations, canopy polygon intersection, isochrones</p></div>
    <div class="sprint-card"><h4>📊 Matplotlib</h4><p>Dark-theme analytics charts, choropleth maps, benchmark panels</p></div>
    <div class="sprint-card"><h4>🌐 Leaflet.js</h4><p>Interactive browser map with 3-route overlay, heatmap GeoJSON layer</p></div>
    <div class="sprint-card"><h4>🐍 Python HTTP Server</h4><p>Lightweight REST API serving routing results and static web files</p></div>
  </div>

  <h2>How to Run</h2>
  <div style="background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:20px;font-family:monospace;font-size:0.9rem;color:var(--green);">
    # Launch interactive web app<br>
    .venv\\Scripts\\python.exe scripts/day5_server.py 8050<br>
    # Open: http://127.0.0.1:8050<br><br>
    # Re-run analytics<br>
    .venv\\Scripts\\python.exe scripts/day7_analytics.py<br>
    .venv\\Scripts\\python.exe scripts/day8_shade_heatmap.py<br>
    .venv\\Scripts\\python.exe scripts/day8_isochrone.py<br>
    .venv\\Scripts\\python.exe scripts/day9_smart_planner.py<br>
    .venv\\Scripts\\python.exe scripts/day9_report_generator.py
  </div>

</div>

<div class="footer">
  <p>🌿 Pune Cooler Routes · 9-Day Sprint · Built with OSM + pybdshadow + Python · {now}</p>
  <p style="margin-top:8px;">Pilot Area: Kothrud → Senapati Bapat Marg → Law College Rd → FC Road · Pune, Maharashtra, India</p>
</div>
</body>
</html>""".format(now=now)

    out = os.path.join(OUTPUTS_DIR, "day9_full_report.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    size_kb = os.path.getsize(out) / 1024
    print(f"  Saved: {out}  ({size_kb:.0f} KB)")
    return out


if __name__ == "__main__":
    print("=" * 60)
    print("  Pune Cooler Routes - Day 9 HTML Report Generator")
    print("=" * 60)
    print("\nBuilding self-contained HTML report...")
    out = build_report()
    print("\n" + "=" * 60)
    print("  Day 9 Report Generator Complete!")
    print(f"  Open: {out}")
    print("=" * 60)
