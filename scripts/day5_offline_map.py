"""
day5_offline_map.py
Generates a standalone, interactive HTML map (outputs/day5_map.html) using Folium.
Features:
- OpenStreetMap and Dark Basemaps
- Pilot area bounding box
- Major Pune landmarks with popup descriptions
- Baseline dual-routes (Fastest in Cyan vs Coolest in Emerald)
- Custom floating comparison HUD with distance, time, and shade metrics
"""
import os
import folium
from day5_engine import CoolerRouter, PUNE_LANDMARKS
from config import BBOX, PT_MIT_WPU, PT_FC, OUTPUTS_DIR

def generate_offline_map():
    print("Generating standalone Day 5 interactive map...")
    router = CoolerRouter()
    
    # Compute routes between MIT-WPU and Fergusson College
    route_res = router.compute_dual_routes(
        orig_lat=PT_MIT_WPU[0], orig_lon=PT_MIT_WPU[1],
        dest_lat=PT_FC[0], dest_lon=PT_FC[1],
        hour=13, coolness_mult=2.5
    )

    center_lat = (BBOX[1] + BBOX[3]) / 2.0
    center_lon = (BBOX[0] + BBOX[2]) / 2.0

    # Create Folium Map with OpenStreetMap base
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles="OpenStreetMap"
    )

    # 1. Add Pilot Bounding Box
    pilot_bounds = [[BBOX[1], BBOX[0]], [BBOX[3], BBOX[2]]]
    folium.Rectangle(
        bounds=pilot_bounds,
        color="#f59e0b",
        weight=2,
        dash_array="6, 6",
        fill=True,
        fill_color="#f59e0b",
        fill_opacity=0.06,
        popup="Pune Pilot Bounding Box (Kothrud to FC Road)"
    ).add_to(m)

    # 2. Add Landmark Markers
    for k, lm in PUNE_LANDMARKS.items():
        folium.CircleMarker(
            location=[lm['lat'], lm['lon']],
            radius=6,
            color="#475569",
            weight=1.5,
            fill=True,
            fill_color="#0f172a",
            fill_opacity=0.9,
            popup=f"<b>{lm['name']}</b>",
            tooltip=lm['name']
        ).add_to(m)

    # 3. Add Fastest Route Polyline (Cyan)
    fast_coords = route_res['fastest']['coordinates']
    folium.PolyLine(
        locations=fast_coords,
        color="#0284c7",
        weight=5,
        opacity=0.85,
        dash_array="8, 6",
        tooltip=f"Fastest Route: {route_res['fastest']['distance_m']}m ({route_res['fastest']['time_min']} min, {route_res['fastest']['shade_pct']}% shade)",
        popup=folium.Popup(
            f"""<div style='font-family:sans-serif; min-width:180px;'>
                 <h4 style='color:#0284c7; margin:0;'>Fastest Route</h4>
                 <b>Distance:</b> {route_res['fastest']['distance_m']} m<br>
                 <b>Walk Time:</b> {route_res['fastest']['time_min']} min<br>
                 <b>Shade:</b> {route_res['fastest']['shade_pct']}%
               </div>""", max_width=250
        )
    ).add_to(m)

    # 4. Add Coolest Route Polyline (Emerald)
    cool_coords = route_res['coolest']['coordinates']
    folium.PolyLine(
        locations=cool_coords,
        color="#10b981",
        weight=6,
        opacity=0.95,
        tooltip=f"Coolest Route: {route_res['coolest']['distance_m']}m ({route_res['coolest']['time_min']} min, {route_res['coolest']['shade_pct']}% shade)",
        popup=folium.Popup(
            f"""<div style='font-family:sans-serif; min-width:180px;'>
                 <h4 style='color:#10b981; margin:0;'>Coolest Route</h4>
                 <b>Distance:</b> {route_res['coolest']['distance_m']} m<br>
                 <b>Walk Time:</b> {route_res['coolest']['time_min']} min<br>
                 <b>Shade:</b> {route_res['coolest']['shade_pct']}% (+{route_res['tradeoff']['shade_gain_pct']}% shade)<br>
                 <small style='color:#059669;'>Maximized tree canopies & narrow building shadows</small>
               </div>""", max_width=250
        )
    ).add_to(m)

    # 5. Add Start & End Markers
    folium.Marker(
        location=[PT_MIT_WPU[0], PT_MIT_WPU[1]],
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
        popup="<b>Start:</b> MIT-WPU Campus"
    ).add_to(m)

    folium.Marker(
        location=[PT_FC[0], PT_FC[1]],
        icon=folium.Icon(color="red", icon="flag", prefix="fa"),
        popup="<b>Destination:</b> Fergusson College"
    ).add_to(m)

    # 6. Add Custom Floating HTML HUD
    hud_html = f"""
    <div style="
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        background: rgba(15, 23, 42, 0.94);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 14px;
        padding: 16px 20px;
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        max-width: 320px;
    ">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
            <span style="font-size:20px;">🌿</span>
            <h3 style="margin:0; font-size:15px; font-weight:700;">Pune Cooler Routes</h3>
        </div>
        <p style="margin:0 0 12px 0; font-size:11px; color:#94a3b8;">MIT-WPU ➔ Fergusson College • 13:00 Midday Sun</p>
        
        <div style="background:rgba(16, 185, 129, 0.12); border-left:3px solid #10b981; padding:8px 10px; border-radius:6px; margin-bottom:12px;">
            <div style="font-size:10px; font-weight:700; color:#10b981; text-transform:uppercase;">Tradeoff Result</div>
            <div style="font-size:12px; font-weight:500; margin-top:2px;">+{route_res['tradeoff']['extra_distance_m']}m (+{route_res['tradeoff']['extra_time_min']} min) gives <b>+{route_res['tradeoff']['shade_gain_pct']}% more shade</b>!</div>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; font-size:11px;">
            <div style="background:rgba(255,255,255,0.04); padding:8px; border-radius:8px; border:1px solid rgba(2,132,199,0.4);">
                <span style="color:#0284c7; font-weight:700;">⚡ FASTEST</span>
                <div style="font-size:14px; font-weight:700; margin-top:2px;">{route_res['fastest']['distance_m']} m</div>
                <div style="color:#94a3b8;">{route_res['fastest']['time_min']} min • {route_res['fastest']['shade_pct']}% shade</div>
            </div>
            <div style="background:rgba(255,255,255,0.04); padding:8px; border-radius:8px; border:1px solid rgba(16,185,129,0.4);">
                <span style="color:#10b981; font-weight:700;">🌿 COOLEST</span>
                <div style="font-size:14px; font-weight:700; margin-top:2px;">{route_res['coolest']['distance_m']} m</div>
                <div style="color:#10b981; font-weight:600;">{route_res['coolest']['time_min']} min • {route_res['coolest']['shade_pct']}% shade</div>
            </div>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(hud_html))

    out_file = os.path.join(OUTPUTS_DIR, "day5_map.html")
    m.save(out_file)
    print(f"Saved standalone interactive map to {out_file}")

if __name__ == "__main__":
    generate_offline_map()
