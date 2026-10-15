/**
 * Pune Cooler Routes - Day 7 Interactive Map Application
 * Adds: Balanced route (3rd polyline), thermal comfort display, routing mode toggle
 */

// Global State
let map;
let landmarks = {};
let startMarker   = null;
let destMarker    = null;
let fastestPolyline  = null;
let coolestPolyline  = null;
let balancedPolyline = null;   // Day 7: balanced route layer
let boundaryPolygon  = null;
let currentRouteData = null;

let selectedHour    = 13;
let selectedCoolness = 2.5;
let selectedMode    = "balanced";   // Day 7 default: Day 6 multi-criteria engine

// Pilot Bounding Box (west, south, east, north)
const PILOT_BBOX = [73.802, 18.495, 73.846, 18.531];

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  loadLandmarks();
  setupEventListeners();
});

/** Initialize Leaflet Map */
function initMap() {
  const centerLat = (PILOT_BBOX[1] + PILOT_BBOX[3]) / 2;
  const centerLon = (PILOT_BBOX[0] + PILOT_BBOX[2]) / 2;

  map = L.map("map", { center: [centerLat, centerLon], zoom: 14, zoomControl: true });

  // Dark Theme Tiles (CartoDB Dark Matter)
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 19
  }).addTo(map);

  // Draw Pilot Bounding Box
  const bounds = [[PILOT_BBOX[1], PILOT_BBOX[0]], [PILOT_BBOX[3], PILOT_BBOX[2]]];
  boundaryPolygon = L.rectangle(bounds, {
    color: "#f59e0b", weight: 2, dashArray: "6, 6",
    fillColor: "#f59e0b", fillOpacity: 0.05
  }).addTo(map);

  map.on("click", onMapClick);
}

/** Handle Map Clicks for Origin & Destination */
function onMapClick(e) {
  const { lat, lng } = e.latlng;

  if (lng < PILOT_BBOX[0] || lng > PILOT_BBOX[2] || lat < PILOT_BBOX[1] || lat > PILOT_BBOX[3]) {
    alert("Please click within the orange pilot bounding box (Kothrud to FC Road).");
    return;
  }

  if (!startMarker) {
    setStartMarker(lat, lng, "Custom Start");
    document.getElementById("startSelect").value = "custom";
  } else if (!destMarker) {
    setDestMarker(lat, lng, "Custom Destination");
    document.getElementById("destSelect").value = "custom";
    calculateRoutes();
  } else {
    setStartMarker(lat, lng, "Custom Start");
    if (destMarker) { map.removeLayer(destMarker); destMarker = null; }
    clearRouteLayers();
  }
}

/** Set Start Marker */
function setStartMarker(lat, lng, title = "Origin") {
  if (startMarker) map.removeLayer(startMarker);
  const icon = L.divIcon({
    className: "custom-marker-start",
    html: `<div style="background:#10b981;width:16px;height:16px;border-radius:50%;border:3px solid #fff;box-shadow:0 0 10px #10b981;"></div>`,
    iconSize: [16, 16], iconAnchor: [8, 8]
  });
  startMarker = L.marker([lat, lng], { icon, draggable: true }).addTo(map)
    .bindPopup(`<b>Start:</b> ${title}`);
  startMarker.on("dragend", () => calculateRoutes());
}

/** Set Destination Marker */
function setDestMarker(lat, lng, title = "Destination") {
  if (destMarker) map.removeLayer(destMarker);
  const icon = L.divIcon({
    className: "custom-marker-dest",
    html: `<div style="background:#ef4444;width:16px;height:16px;border-radius:50%;border:3px solid #fff;box-shadow:0 0 10px #ef4444;"></div>`,
    iconSize: [16, 16], iconAnchor: [8, 8]
  });
  destMarker = L.marker([lat, lng], { icon, draggable: true }).addTo(map)
    .bindPopup(`<b>Destination:</b> ${title}`);
  destMarker.on("dragend", () => calculateRoutes());
}

/** Fetch Landmarks from Backend */
async function loadLandmarks() {
  try {
    const res = await fetch("/api/landmarks");
    if (!res.ok) throw new Error("Failed to fetch landmarks");
    landmarks = await res.json();

    const startSelect = document.getElementById("startSelect");
    const destSelect  = document.getElementById("destSelect");

    startSelect.innerHTML = `<option value="custom">📍 Custom Map Pin</option>`;
    destSelect.innerHTML  = `<option value="custom">📍 Custom Map Pin</option>`;

    for (const [key, item] of Object.entries(landmarks)) {
      startSelect.innerHTML += `<option value="${key}">${item.name}</option>`;
      destSelect.innerHTML  += `<option value="${key}">${item.name}</option>`;
    }

    startSelect.value = "mit_wpu";
    destSelect.value  = "fergusson";
    applyLandmarkSelection();
    calculateRoutes();
  } catch (err) {
    console.error("Error loading landmarks:", err);
  }
}

/** Apply Landmark Selection from Dropdowns */
function applyLandmarkSelection() {
  const startKey = document.getElementById("startSelect").value;
  const destKey  = document.getElementById("destSelect").value;
  if (startKey && landmarks[startKey]) {
    const lm = landmarks[startKey];
    setStartMarker(lm.lat, lm.lon, lm.name);
  }
  if (destKey && landmarks[destKey]) {
    const lm = landmarks[destKey];
    setDestMarker(lm.lat, lm.lon, lm.name);
  }
}

/** Calculate Routes via Backend API */
async function calculateRoutes() {
  if (!startMarker || !destMarker) return;

  const startLatLng = startMarker.getLatLng();
  const destLatLng  = destMarker.getLatLng();

  const btn = document.getElementById("findRoutesBtn");
  btn.innerHTML = `<span class="btn-icon">⏳</span> Computing...`;
  btn.disabled = true;

  // Build URL with mode parameter
  const url = `/api/route?start_lat=${startLatLng.lat}&start_lon=${startLatLng.lng}` +
              `&dest_lat=${destLatLng.lat}&dest_lon=${destLatLng.lng}` +
              `&hour=${selectedHour}&coolness=${selectedCoolness}&mode=${selectedMode}`;

  try {
    const res = await fetch(url);
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.error || "Failed to calculate route");
    }
    currentRouteData = await res.json();
    renderRoutesOnMap(currentRouteData);
    renderMetrics(currentRouteData);
  } catch (err) {
    alert("Routing Error: " + err.message);
  } finally {
    btn.innerHTML = `<span class="btn-icon">⚡</span> Calculate Routes`;
    btn.disabled = false;
  }
}

/** Render Route Polylines on Leaflet Map */
function renderRoutesOnMap(data) {
  clearRouteLayers();

  const fastCoords = data.fastest ? data.fastest.coordinates : null;
  const coolCoords = data.coolest ? data.coolest.coordinates : null;
  const balCoords  = data.balanced ? data.balanced.coordinates : null;

  // Fastest Route (Cyan Dashed)
  if (fastCoords && fastCoords.length > 1) {
    fastestPolyline = L.polyline(fastCoords, {
      color: "#06b6d4", weight: 5, opacity: 0.85, dashArray: "8, 6", lineJoin: "round"
    }).addTo(map);
    fastestPolyline.bindPopup(`
      <b>⚡ Fastest Walking Route</b><br>
      Distance: ${data.fastest.distance_m} m<br>
      Time: ${data.fastest.time_min} min<br>
      Shade: ${data.fastest.shade_pct}%
    `);
  }

  // Balanced Route (Purple) - Day 7
  if (balCoords && balCoords.length > 1) {
    balancedPolyline = L.polyline(balCoords, {
      color: "#a78bfa", weight: 5, opacity: 0.85, dashArray: "4, 4", lineJoin: "round"
    }).addTo(map);
    balancedPolyline.bindPopup(`
      <b>🛡️ Balanced Route (Cool + Safe)</b><br>
      Distance: ${data.balanced.distance_m} m<br>
      Time: ${data.balanced.time_min} min<br>
      Shade: ${data.balanced.shade_pct}%
    `);
    document.getElementById("legendBalanced").style.display = "flex";
  } else {
    document.getElementById("legendBalanced").style.display = "none";
  }

  // Coolest Route (Emerald Glow)
  if (coolCoords && coolCoords.length > 1) {
    coolestPolyline = L.polyline(coolCoords, {
      color: "#10b981", weight: 6, opacity: 0.95, lineJoin: "round"
    }).addTo(map);
    coolestPolyline.bindPopup(`
      <b>🌿 Coolest Shaded Route</b><br>
      Distance: ${data.coolest.distance_m} m<br>
      Time: ${data.coolest.time_min} min<br>
      Shade: ${data.coolest.shade_pct}% (Maximized Tree/Building Shade)
    `);
  }

  // Fit map to show all routes
  const layers = [fastestPolyline, balancedPolyline, coolestPolyline].filter(Boolean);
  if (layers.length > 0) {
    const group = new L.featureGroup(layers);
    map.fitBounds(group.getBounds(), { padding: [50, 50] });
  }
}

/** Clear existing polylines */
function clearRouteLayers() {
  [fastestPolyline, coolestPolyline, balancedPolyline].forEach(p => {
    if (p) map.removeLayer(p);
  });
  fastestPolyline  = null;
  coolestPolyline  = null;
  balancedPolyline = null;
}

/** Render Comparison Metrics in DOM */
function renderMetrics(data) {
  const isDay6 = data.fastest && data.coolest && data.balanced !== undefined;

  // Fastest Card (always present)
  if (data.fastest) {
    document.getElementById("fastDist").innerText     = `${data.fastest.distance_m} m`;
    document.getElementById("fastTime").innerText     = `${data.fastest.time_min} min`;
    document.getElementById("fastShadePct").innerText = `${data.fastest.shade_pct}%`;
    document.getElementById("fastShadeBar").style.width = `${Math.min(100, data.fastest.shade_pct)}%`;
  }

  // Coolest Card
  if (data.coolest) {
    document.getElementById("coolDist").innerText     = `${data.coolest.distance_m} m`;
    document.getElementById("coolTime").innerText     = `${data.coolest.time_min} min`;
    document.getElementById("coolShadePct").innerText = `${data.coolest.shade_pct}%`;
    document.getElementById("coolShadeBar").style.width = `${Math.min(100, data.coolest.shade_pct)}%`;
  }

  // Balanced Card (Day 6 multi-criteria engine)
  const balCard = document.getElementById("balancedCard");
  if (data.balanced) {
    balCard.style.display = "";
    document.getElementById("balDist").innerText     = `${data.balanced.distance_m} m`;
    document.getElementById("balTime").innerText     = `${data.balanced.time_min} min`;
    document.getElementById("balShadePct").innerText = `${data.balanced.shade_pct}%`;
    document.getElementById("balShadeBar").style.width = `${Math.min(100, data.balanced.shade_pct)}%`;
  } else {
    balCard.style.display = "none";
  }

  // Tradeoff Verdict Banner
  if (data.tradeoff) {
    const verdict = data.tradeoff.verdict || "";
    document.getElementById("tradeoffVerdict").innerText = verdict;
    document.getElementById("deltaDist").innerText  = `+${data.tradeoff.extra_distance_m} m`;
    document.getElementById("deltaTime").innerText  = `+${data.tradeoff.extra_time_min} min`;
    document.getElementById("deltaShade").innerText = `+${data.tradeoff.shade_gain_pct}%`;
  } else if (data.comparison) {
    // Day 6 multi-criteria comparison object
    const c = data.comparison;
    document.getElementById("tradeoffVerdict").innerText =
      `Coolest route gains +${c.shade_gain_vs_fast}% shade with only +${c.detour_min_cool} min detour.`;
    document.getElementById("deltaDist").innerText  = `+${c.detour_m_cool} m`;
    document.getElementById("deltaTime").innerText  = `+${c.detour_min_cool} min`;
    document.getElementById("deltaShade").innerText = `+${c.shade_gain_vs_fast}%`;
  }

  // Thermal Comfort Panel (Day 7) - only shown for Day 6 engine results
  const thermalPanel = document.getElementById("thermalPanel");
  if (data.coolest && data.coolest.apparent_temp_relief_c !== undefined) {
    thermalPanel.style.display = "";
    document.getElementById("thermalRelief").innerText =
      `-${data.coolest.apparent_temp_relief_c}°C apparent temp relief`;
    const heatReduced = data.comparison
      ? data.comparison.heat_reduction_w_m2
      : (data.fastest && data.coolest
          ? (data.fastest.heat_exposure_w_m2 - data.coolest.heat_exposure_w_m2).toFixed(1)
          : 0);
    document.getElementById("heatAvoided").innerText = `${heatReduced} W/m² avoided`;
  } else {
    thermalPanel.style.display = "none";
  }

  // Turn-by-Turn Steps for Coolest Route with advisory text (Day 7 enhancement)
  const stepsList = document.getElementById("stepsList");
  stepsList.innerHTML = "";
  const steps = (data.coolest || data.fastest || {}).steps || [];
  steps.forEach(step => {
    const div = document.createElement("div");
    div.className = `step-item ${step.is_shaded ? "shaded" : ""}`;
    const advisory = step.advisory || "";
    div.innerHTML = `
      <div class="step-street">${step.is_shaded ? "🌳" : "☀️"} ${step.street}</div>
      <div class="step-meta">
        <span>${step.length_m} m</span>
        <strong>${step.shade_pct}% shade</strong>
      </div>
      ${advisory ? `<div class="step-advisory">${advisory}</div>` : ""}
    `;
    stepsList.appendChild(div);
  });
}

/** Setup Event Listeners */
function setupEventListeners() {
  // Preset Chips
  document.querySelectorAll(".preset-chips .chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".preset-chips .chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      document.getElementById("startSelect").value = chip.getAttribute("data-from");
      document.getElementById("destSelect").value  = chip.getAttribute("data-to");
      applyLandmarkSelection();
      calculateRoutes();
    });
  });

  // Dropdown Changes
  ["startSelect", "destSelect"].forEach(id => {
    document.getElementById(id).addEventListener("change", () => {
      applyLandmarkSelection();
      calculateRoutes();
    });
  });

  // Swap Locations
  document.getElementById("swapLocationsBtn").addEventListener("click", () => {
    const s = document.getElementById("startSelect");
    const d = document.getElementById("destSelect");
    const tmp = s.value; s.value = d.value; d.value = tmp;
    applyLandmarkSelection();
    calculateRoutes();
  });

  // Time Buttons
  document.querySelectorAll(".time-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".time-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const h = btn.getAttribute("data-hour");
      if (h === "live") {
        selectedHour = new Date().getHours();
        document.getElementById("timeLabel").innerText = `${selectedHour}:00 (Live Wall Clock)`;
      } else {
        selectedHour = parseInt(h);
        const labels = { 9: "09:00 (Morning Sun)", 13: "13:00 (Midday Sun)", 16: "16:00 (Afternoon Sun)" };
        document.getElementById("timeLabel").innerText = labels[selectedHour] || `${selectedHour}:00`;
      }
      calculateRoutes();
    });
  });

  // Routing Mode Toggle (Day 7)
  document.querySelectorAll(".mode-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedMode = btn.getAttribute("data-mode");
      calculateRoutes();
    });
  });

  // Coolness Slider
  const slider = document.getElementById("coolnessSlider");
  slider.addEventListener("input", e => {
    selectedCoolness = parseFloat(e.target.value);
    document.getElementById("coolnessVal").innerText = `${selectedCoolness}x`;
  });
  slider.addEventListener("change", () => calculateRoutes());

  // Calculate Button
  document.getElementById("findRoutesBtn").addEventListener("click", () => calculateRoutes());

  // Toggle Steps Accordion
  document.getElementById("toggleStepsBtn").addEventListener("click", () => {
    const list  = document.getElementById("stepsList");
    const arrow = document.querySelector(".accordion-arrow");
    const isHidden = list.style.display === "none";
    list.style.display  = isHidden ? "flex" : "none";
    arrow.innerText     = isHidden ? "▼" : "▶";
  });

  // Export GeoJSON
  document.getElementById("exportGeoJsonBtn").addEventListener("click", () => {
    if (!currentRouteData) { alert("Please calculate routes first."); return; }

    const features = [];
    const routes = [
      { key: "fastest",  label: "Fastest",  color: "#06b6d4" },
      { key: "balanced", label: "Balanced (Cool+Safe)", color: "#a78bfa" },
      { key: "coolest",  label: "Coolest",  color: "#10b981" },
    ];
    routes.forEach(r => {
      const rd = currentRouteData[r.key];
      if (!rd) return;
      features.push({
        type: "Feature",
        properties: {
          route_type: r.label, color: r.color,
          distance_m: rd.distance_m, time_min: rd.time_min, shade_pct: rd.shade_pct
        },
        geometry: { type: "LineString", coordinates: rd.geojson_coords || [] }
      });
    });

    const geojson = { type: "FeatureCollection", features };
    const blob    = new Blob([JSON.stringify(geojson, null, 2)], { type: "application/json" });
    const url     = URL.createObjectURL(blob);
    const a       = document.createElement("a");
    a.href        = url;
    a.download    = `pune_cooler_routes_day7_${selectedHour}00.geojson`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // Reset Pins
  document.getElementById("resetPinsBtn").addEventListener("click", () => {
    [startMarker, destMarker].forEach(m => { if (m) map.removeLayer(m); });
    startMarker = null; destMarker = null;
    clearRouteLayers();
    document.getElementById("startSelect").value = "custom";
    document.getElementById("destSelect").value  = "custom";
    alert("Pins cleared! Click anywhere in the orange pilot box to set a new Start pin.");
  });
}


// ============================================================
// Day 8 & 9: Heatmap, Isochrone, Route History, Share URL
// ============================================================

// Layer state
let heatmapLayer   = null;
let heatmapActive  = false;
let isochroneLayerStd = null;
let isochroneLayerShd = null;
let isochroneActive  = false;

// Route history (stored in memory, max 5)
let routeHistory = [];

/** ---- Heatmap Overlay (Day 8) ---- */
function toggleHeatmap() {
  const sw = document.getElementById("heatmapToggle");
  if (heatmapActive) {
    if (heatmapLayer) { map.removeLayer(heatmapLayer); heatmapLayer = null; }
    sw.classList.remove("on");
    heatmapActive = false;
  } else {
    loadHeatmapLayer();
  }
}

function loadHeatmapLayer() {
  const sw = document.getElementById("heatmapToggle");
  sw.style.opacity = "0.5";

  fetch("/outputs/day8_heatmap.geojson")
    .then(r => r.json())
    .then(data => {
      const slot = selectedHour < 11 ? "shade_0900" : selectedHour < 15 ? "shade_1300" : "shade_1600";
      heatmapLayer = L.geoJSON(data, {
        style: feature => {
          const shade = feature.properties[slot] || feature.properties.composite || 0;
          const color = shadeToColor(shade);
          return { color, weight: 2.5, opacity: 0.75 };
        },
        onEachFeature: (feature, layer) => {
          const p = feature.properties;
          layer.bindTooltip(
            `<b>${p.name}</b><br>
             09:00: ${(p.shade_0900 * 100).toFixed(1)}% shade<br>
             13:00: ${(p.shade_1300 * 100).toFixed(1)}% shade<br>
             16:00: ${(p.shade_1600 * 100).toFixed(1)}% shade<br>
             🌿 Tree Bonus: ${(p.tree_bonus * 100).toFixed(1)}%<br>
             Composite: ${(p.composite * 100).toFixed(1)}%`,
            { sticky: true, className: "heatmap-tooltip" }
          );
        }
      }).addTo(map);
      sw.classList.add("on");
      sw.style.opacity = "1";
      heatmapActive = true;
    })
    .catch(err => {
      console.warn("Heatmap GeoJSON not yet available:", err);
      sw.style.opacity = "1";
      alert("Heatmap not yet generated. Run scripts/day8_shade_heatmap.py first.");
    });
}

function shadeToColor(shade) {
  // 0 = full sun (red), 0.5 = partial (amber), 1 = full shade (green)
  if (shade >= 0.55) return "#10b981";   // deep green
  if (shade >= 0.40) return "#34d399";   // light green
  if (shade >= 0.30) return "#fbbf24";   // amber
  if (shade >= 0.18) return "#f97316";   // orange
  return "#ef4444";                       // red
}

/** ---- Isochrone Overlay (Day 8) ---- */
function toggleIsochrone() {
  const sw = document.getElementById("isochroneToggle");
  if (isochroneActive) {
    if (isochroneLayerStd) { map.removeLayer(isochroneLayerStd); isochroneLayerStd = null; }
    if (isochroneLayerShd) { map.removeLayer(isochroneLayerShd); isochroneLayerShd = null; }
    sw.classList.remove("on");
    isochroneActive = false;
  } else {
    loadIsochroneLayers();
  }
}

function loadIsochroneLayers() {
  const sw = document.getElementById("isochroneToggle");
  sw.style.opacity = "0.5";
  const bandColors = ["#10b981", "#f59e0b", "#ef4444"];
  const bandAlphas = [0.12, 0.09, 0.06];

  Promise.all([
    fetch("/outputs/day8_isochrone_shaded.geojson").then(r => r.json()),
  ]).then(([shadedData]) => {
    isochroneLayerShd = L.geoJSON(shadedData, {
      style: feature => {
        const idx = [5, 10, 15].indexOf(feature.properties.time_band_min);
        return {
          color: bandColors[idx] || "#fff",
          weight: 2.0,
          opacity: 0.7,
          fillColor: bandColors[idx] || "#fff",
          fillOpacity: bandAlphas[idx] || 0.08,
          dashArray: "6, 4"
        };
      },
      onEachFeature: (feature, layer) => {
        layer.bindTooltip(
          `<b>Shade-Priority Isochrone</b><br>${feature.properties.time_band_min}-minute walking zone`,
          { sticky: false }
        );
      }
    }).addTo(map);
    sw.classList.add("on");
    sw.style.opacity = "1";
    isochroneActive = true;
  }).catch(err => {
    console.warn("Isochrone GeoJSON not available:", err);
    sw.style.opacity = "1";
    alert("Isochrone data not yet generated. Run scripts/day8_isochrone.py first.");
  });
}

/** ---- Route History (Day 9) ---- */
function addToHistory(data) {
  const fastest = data.fastest || {};
  const coolest = data.coolest || {};
  const startName = document.getElementById("startSelect").options[document.getElementById("startSelect").selectedIndex]?.text || "Custom";
  const destName  = document.getElementById("destSelect").options[document.getElementById("destSelect").selectedIndex]?.text  || "Custom";

  const entry = {
    from: startName,
    to:   destName,
    time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    hour: selectedHour,
    fastest_shade: fastest.shade_pct || 0,
    coolest_shade: coolest.shade_pct || 0,
    coolest_dist:  coolest.distance_m || 0,
    data: data   // store full data for replay
  };
  routeHistory.unshift(entry);
  if (routeHistory.length > 5) routeHistory.pop();
  renderHistory();
}

function renderHistory() {
  const list = document.getElementById("historyList");
  if (!list) return;
  if (routeHistory.length === 0) {
    list.innerHTML = '<div class="history-empty">No routes calculated yet.</div>';
    return;
  }
  list.innerHTML = routeHistory.map((e, i) => `
    <div class="history-item" onclick="replayHistory(${i})">
      <div class="h-route">${e.from} → ${e.to}</div>
      <div class="h-meta">
        🕐 ${e.time} &nbsp;|&nbsp; ⏰ ${e.hour}:00
        &nbsp;|&nbsp; 🌿 <span class="h-shade">${e.coolest_shade}%</span> shade
        &nbsp;|&nbsp; ${e.coolest_dist}m
      </div>
    </div>
  `).join("");
}

function replayHistory(idx) {
  const entry = routeHistory[idx];
  if (!entry || !entry.data) return;
  currentRouteData = entry.data;
  drawRoutePolylines(entry.data);
  renderMetrics(entry.data);
}

/** ---- Share Route URL (Day 9) ---- */
function shareRouteURL() {
  if (!startMarker || !destMarker) {
    alert("Calculate a route first, then share.");
    return;
  }
  const s = startMarker.getLatLng();
  const d = destMarker.getLatLng();
  const hash = `#r/${s.lat.toFixed(5)},${s.lng.toFixed(5)}/${d.lat.toFixed(5)},${d.lng.toFixed(5)}/${selectedHour}/${selectedMode}`;
  const url  = window.location.origin + window.location.pathname + hash;

  if (navigator.clipboard) {
    navigator.clipboard.writeText(url).then(() => {
      const btn = document.getElementById("shareRouteBtn");
      const old = btn.innerHTML;
      btn.innerHTML = "✅ URL Copied!";
      btn.style.color = "#10b981";
      setTimeout(() => { btn.innerHTML = old; btn.style.color = ""; }, 2500);
    });
  } else {
    prompt("Copy this route URL:", url);
  }
}

/** Restore route from URL hash on load */
function restoreFromHash() {
  const hash = window.location.hash;
  const match = hash.match(/^#r\/([-\d.]+),([-\d.]+)\/([-\d.]+),([-\d.]+)\/(\d+)\/(\w+)/);
  if (!match) return;
  const [, sLat, sLon, dLat, dLon, hour, mode] = match;
  // Restore hour
  selectedHour = parseInt(hour);
  document.querySelectorAll(".time-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.hour == hour);
  });
  // Restore mode
  selectedMode = mode;
  document.querySelectorAll(".mode-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.mode === mode);
  });
  // Place markers and calculate
  setStartMarker(parseFloat(sLat), parseFloat(sLon), "Shared Start");
  setDestMarker(parseFloat(dLat), parseFloat(dLon), "Shared Destination");
  setTimeout(() => calculateRoutes(), 500);
}

/** ---- Load Waypoint Recommendations (Day 9) ---- */
async function loadWaypointRecommendations() {
  try {
    const res = await fetch("/api/waypoint_recommendations");
    if (!res.ok) return;
    const data = await res.json();
    if (!data || data.length === 0) return;

    const panel = document.getElementById("waypointPanel");
    const list  = document.getElementById("waypointList");
    if (!panel || !list) return;

    const top3 = data.slice(0, 3);
    list.innerHTML = top3.map(wp => `
      <div class="waypoint-item">
        📍 <b>${wp.waypoint}</b><br>
        <span class="wp-gain">+${wp.shade_gain_pct}% shade</span>
        <span class="wp-cost"> · +${wp.detour_m}m · +${wp.detour_min}min</span>
      </div>
    `).join("");
    panel.classList.add("visible");
  } catch (e) {
    console.warn("Waypoints not available:", e);
  }
}

// ---- Hook into existing calculateRoutes to add history + share ----
const _origCalculateRoutes = calculateRoutes;
calculateRoutes = async function() {
  await _origCalculateRoutes.apply(this, arguments);
  // After successful calculation, add to history
  if (currentRouteData) {
    addToHistory(currentRouteData);
    updateShareButton();
  }
};

function updateShareButton() {
  const btn = document.getElementById("shareRouteBtn");
  if (btn) {
    btn.addEventListener("click", shareRouteURL);
  }
}

// ---- Init on DOMContentLoaded extensions ----
document.addEventListener("DOMContentLoaded", () => {
  restoreFromHash();
  loadWaypointRecommendations();
  renderHistory();

  // Wire up share button
  const shareBtn = document.getElementById("shareRouteBtn");
  if (shareBtn) {
    shareBtn.addEventListener("click", shareRouteURL);
  }
});
