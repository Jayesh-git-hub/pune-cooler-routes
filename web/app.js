/**
 * Pune Cooler Routes - Google Maps Style Application
 * Features:
 * - Esri World Street Map (Google Maps lookalike) + Satellite + Terrain + Humanitarian
 * - Google Maps Floating Search & Directions Drawer
 * - Dual-cased prominent route polylines & Google SVG pins
 * - Interactive Turn-by-Turn Navigation Banner & Virtual Walker HUD
 * - Topography, Clean-Air ETHI, and PWA integration
 */

function extractCoords(routeObj) {
  if (!routeObj) return null;
  if (routeObj.coordinates && routeObj.coordinates.length > 0) {
    return routeObj.coordinates;
  }
  if (routeObj.geojson && routeObj.geojson.coordinates) {
    return routeObj.geojson.coordinates.map(pt => [pt[1], pt[0]]);
  }
  return null;
}

// Global Application State
let map;
let landmarks = {};
let startMarker = null;
let destMarker = null;

// Route Polylines & Casings (Google Maps style)
let fastestPolyline = null;
let fastestCasing = null;
let coolestPolyline = null;
let coolestCasing = null;
let balancedPolyline = null;
let balancedCasing = null;
let boundaryPolygon = null;

let currentRouteData = null;
let activeRouteType = "coolest";

let selectedHour = 13;
let selectedCoolness = 2.5;
let selectedMode = "dynamic";

// Pilot Bounding Box (Kothrud to FC Road)
const PILOT_BBOX = [73.802, 18.495, 73.846, 18.531];

let baseLayers = {};
let currentBaseLayer = null;

// Map Overlays
let heatmapLayer = null;
let heatmapActive = false;
let isochroneLayerShd = null;
let isochroneActive = false;

// Navigation & Simulation State
let walkerMarker = null;
let simInterval = null;
let simIndex = 0;
let simCoords = [];
let simSpeed = 1;
let simIsPlaying = false;
let simElapsedSeconds = 0;
let currentStepIndex = 0;
let routeHistory = [];

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  loadLandmarks();
  setupEventListeners();
  registerServiceWorker();
});

/** Initialize Leaflet Map with Google Maps-like Basemap */
function initMap() {
  const centerLat = (PILOT_BBOX[1] + PILOT_BBOX[3]) / 2;
  const centerLon = (PILOT_BBOX[0] + PILOT_BBOX[2]) / 2;

  map = L.map("map", {
    center: [centerLat, centerLon],
    zoom: 14,
    zoomControl: false,
    attributionControl: true
  });

  // 1. Google Maps lookalike (Esri World Street Map)
  baseLayers.streets = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", {
    attribution: "Map &copy; Esri, HERE, Garmin, OpenStreetMap",
    maxZoom: 19
  });

  // 2. High-Res Satellite
  baseLayers.satellite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
    attribution: "Imagery &copy; Esri, Maxar",
    maxZoom: 19
  });

  // 3. Topo Terrain
  baseLayers.terrain = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", {
    attribution: "Topo &copy; Esri, USGS",
    maxZoom: 19
  });

  // 4. OSM Walking
  baseLayers.humanitarian = L.tileLayer("https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19
  });

  currentBaseLayer = baseLayers.streets;
  currentBaseLayer.addTo(map);

  const bounds = [[PILOT_BBOX[1], PILOT_BBOX[0]], [PILOT_BBOX[3], PILOT_BBOX[2]]];
  boundaryPolygon = L.rectangle(bounds, {
    color: "#f29900",
    weight: 2,
    dashArray: "6, 6",
    fillColor: "#f29900",
    fillOpacity: 0.04
  }).addTo(map);

  map.on("click", onMapClick);
}

function switchBasemap(layerName) {
  if (!baseLayers[layerName]) return;
  if (currentBaseLayer) map.removeLayer(currentBaseLayer);
  currentBaseLayer = baseLayers[layerName];
  currentBaseLayer.addTo(map);

  document.querySelectorAll(".layer-option").forEach(opt => {
    opt.classList.toggle("active", opt.dataset.layer === layerName);
  });
}

function onMapClick(e) {
  const { lat, lng } = e.latlng;
  if (lng < PILOT_BBOX[0] || lng > PILOT_BBOX[2] || lat < PILOT_BBOX[1] || lat > PILOT_BBOX[3]) {
    alert("Please click within the orange pilot bounding box (Kothrud to FC Road).");
    return;
  }

  if (!startMarker) {
    setStartMarker(lat, lng, "Custom Start Pin");
    const s = document.getElementById("startSelect");
    if (s) s.value = "custom";
  } else if (!destMarker) {
    setDestMarker(lat, lng, "Custom Destination Pin");
    const d = document.getElementById("destSelect");
    if (d) d.value = "custom";
    calculateRoutes();
  } else {
    setStartMarker(lat, lng, "Custom Start Pin");
    if (destMarker) { map.removeLayer(destMarker); destMarker = null; }
    clearRouteLayers();
  }
}

function setStartMarker(lat, lng, title = "Origin") {
  if (startMarker) map.removeLayer(startMarker);
  const icon = L.divIcon({
    className: "gmaps-origin-marker",
    html: '<div style="position:relative;width:24px;height:24px;display:flex;align-items:center;justify-content:center;"><div style="position:absolute;width:24px;height:24px;border-radius:50%;background:rgba(26,115,232,0.3);animation:gmapsPulse 1.8s infinite;"></div><div style="width:14px;height:14px;border-radius:50%;background:#1a73e8;border:3px solid #ffffff;box-shadow:0 2px 6px rgba(0,0,0,0.35);"></div></div>',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });
  startMarker = L.marker([lat, lng], { icon, draggable: true }).addTo(map)
    .bindPopup(`<b>Start:</b> ${title}`);
  startMarker.on("dragend", () => calculateRoutes());
}

function setDestMarker(lat, lng, title = "Destination") {
  if (destMarker) map.removeLayer(destMarker);
  const icon = L.divIcon({
    className: "gmaps-dest-marker",
    html: '<div style="position:relative;width:32px;height:40px;"><svg viewBox="0 0 24 24" width="32" height="40" style="filter:drop-shadow(0 3px 6px rgba(0,0,0,0.38));"><path fill="#ea4335" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/><circle cx="12" cy="9" r="3" fill="#ffffff"/></svg></div>',
    iconSize: [32, 40],
    iconAnchor: [16, 40]
  });
  destMarker = L.marker([lat, lng], { icon, draggable: true }).addTo(map)
    .bindPopup(`<b>Destination:</b> ${title}`);
  destMarker.on("dragend", () => calculateRoutes());
}

async function loadLandmarks() {
  try {
    const res = await fetch("/api/landmarks");
    if (!res.ok) throw new Error("Failed to fetch landmarks");
    landmarks = await res.json();

    const startSelect = document.getElementById("startSelect");
    const destSelect  = document.getElementById("destSelect");

    startSelect.innerHTML = '<option value="custom">📍 Custom Map Pin</option>';
    destSelect.innerHTML  = '<option value="custom">📍 Custom Map Pin</option>';

    for (const [key, item] of Object.entries(landmarks)) {
      startSelect.innerHTML += `<option value="${key}">📍 ${item.name}</option>`;
      destSelect.innerHTML  += `<option value="${key}">📍 ${item.name}</option>`;
    }

    startSelect.value = "mit_wpu";
    destSelect.value  = "fergusson";
    applyLandmarkSelection();
    calculateRoutes();
  } catch (err) {
    console.error("Error loading landmarks:", err);
  }
}

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

async function calculateRoutes() {
  if (!startMarker || !destMarker) return;

  const startLatLng = startMarker.getLatLng();
  const destLatLng  = destMarker.getLatLng();

  const btn = document.getElementById("findRoutesBtn");
  btn.innerHTML = '<span>⏳ Finding Cooler Routes...</span>';
  btn.disabled = true;

  const customTimeElem = document.getElementById("customTimeInput");
  const timeQueryVal = (customTimeElem && customTimeElem.value) ? customTimeElem.value : `${selectedHour}:00`;
  const url = `/api/route?start_lat=${startLatLng.lat}&start_lon=${startLatLng.lng}` +
              `&dest_lat=${destLatLng.lat}&dest_lon=${destLatLng.lng}` +
              `&hour=${selectedHour}&time=${timeQueryVal}&coolness=${selectedCoolness}&mode=${selectedMode}`;

  try {
    const res = await fetch(url);
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.error || "Failed to calculate route");
    }
    currentRouteData = await res.json();
    renderRoutesOnMap(currentRouteData);
    renderMetrics(currentRouteData);
    addToHistory(currentRouteData);

    const resultsSec = document.getElementById("resultsSection");
    if (resultsSec) resultsSec.style.display = "flex";
  } catch (err) {
    alert("Routing Error: " + err.message);
  } finally {
    btn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71z"/></svg><span>Find Cooler Routes</span>';
    btn.disabled = false;
  }
}

function renderRoutesOnMap(data) {
  clearRouteLayers();

  const fastCoords = extractCoords(data.fastest);
  const coolCoords = extractCoords(data.coolest);
  const balCoords  = extractCoords(data.balanced);

  // 1. Fastest Route (Direct Red / Orange)
  if (fastCoords && fastCoords.length > 1) {
    fastestCasing = L.polyline(fastCoords, {
      color: "#ffffff", weight: 8, opacity: 0.8, lineJoin: "round", lineCap: "round"
    }).addTo(map);
    fastestPolyline = L.polyline(fastCoords, {
      color: "#ea4335", weight: 4.5, opacity: 0.85, dashArray: "4, 6", lineJoin: "round", lineCap: "round"
    }).addTo(map);
    fastestPolyline.bindPopup(`<b>⚡ Fastest Route</b><br>${data.fastest.distance_m} m • ${data.fastest.time_min} min • ${data.fastest.shade_pct}% shade`);
  }

  // 2. Balanced Route (Safe + Cool Purple)
  if (balCoords && balCoords.length > 1) {
    balancedCasing = L.polyline(balCoords, {
      color: "#ffffff", weight: 9, opacity: 0.85, lineJoin: "round", lineCap: "round"
    }).addTo(map);
    balancedPolyline = L.polyline(balCoords, {
      color: "#8430ce", weight: 5, opacity: 0.9, dashArray: "6, 6", lineJoin: "round", lineCap: "round"
    }).addTo(map);
    balancedPolyline.bindPopup(`<b>🛡️ Balanced Route</b><br>${data.balanced.distance_m} m • ${data.balanced.time_min} min • ${data.balanced.shade_pct}% shade`);
    const legBal = document.getElementById("legendBalanced");
    if (legBal) legBal.style.display = "flex";
  }

  // 3. Coolest Route (Google Green - Solid with White Casing)
  if (coolCoords && coolCoords.length > 1) {
    coolestCasing = L.polyline(coolCoords, {
      color: "#ffffff", weight: 11, opacity: 0.95, lineJoin: "round", lineCap: "round"
    }).addTo(map);
    coolestPolyline = L.polyline(coolCoords, {
      color: "#0F9D58", weight: 6.5, opacity: 1.0, lineJoin: "round", lineCap: "round"
    }).addTo(map);
    coolestPolyline.bindPopup(`<b>🌿 Coolest Shaded Route (Recommended)</b><br>${data.coolest.distance_m} m • ${data.coolest.time_min} min • ${data.coolest.shade_pct}% tree & building shade`);
  }

  const layers = [fastestPolyline, balancedPolyline, coolestPolyline].filter(Boolean);
  if (layers.length > 0) {
    const group = new L.featureGroup(layers);
    map.fitBounds(group.getBounds(), { padding: [60, 60] });
  }

  highlightActiveRoute("coolest");
}

function highlightActiveRoute(type) {
  activeRouteType = type;
  document.querySelectorAll(".gmaps-route-card").forEach(c => c.classList.remove("active"));

  if (type === "coolest") {
    const c = document.getElementById("coolestRouteCard");
    if (c) c.classList.add("active");
    if (coolestPolyline) coolestPolyline.bringToFront();
  } else if (type === "balanced") {
    const c = document.getElementById("balancedCard");
    if (c) c.classList.add("active");
    if (balancedPolyline) balancedPolyline.bringToFront();
  } else if (type === "fastest") {
    const c = document.getElementById("fastestRouteCard");
    if (c) c.classList.add("active");
    if (fastestPolyline) fastestPolyline.bringToFront();
  }
}

function clearRouteLayers() {
  [fastestCasing, fastestPolyline, coolestCasing, coolestPolyline, balancedCasing, balancedPolyline].forEach(p => {
    if (p) map.removeLayer(p);
  });
  fastestCasing = null; fastestPolyline = null;
  coolestCasing = null; coolestPolyline = null;
  balancedCasing = null; balancedPolyline = null;
}

function renderMetrics(data) {
  if (data.fastest) {
    const fd = document.getElementById("fastDist");
    const ft = document.getElementById("fastTime");
    const fs = document.getElementById("fastShadePct");
    const fb = document.getElementById("fastShadeBar");
    if (fd) fd.innerText = `${data.fastest.distance_m} m`;
    if (ft) ft.innerText = `${data.fastest.time_min} min`;
    if (fs) fs.innerText = `${data.fastest.shade_pct}%`;
    if (fb) fb.style.width = `${Math.min(100, data.fastest.shade_pct)}%`;
  }

  if (data.coolest) {
    const cd = document.getElementById("coolDist");
    const ct = document.getElementById("coolTime");
    const cs = document.getElementById("coolShadePct");
    const cb = document.getElementById("coolShadeBar");
    if (cd) cd.innerText = `${(data.coolest.distance_m / 1000).toFixed(1)} km (${data.coolest.distance_m}m)`;
    if (ct) ct.innerText = `${data.coolest.time_min} min`;
    if (cs) cs.innerText = `${data.coolest.shade_pct}%`;
    if (cb) cb.style.width = `${Math.min(100, data.coolest.shade_pct)}%`;
  }

  const balCard = document.getElementById("balancedCard");
  if (data.balanced) {
    if (balCard) balCard.style.display = "";
    const bd = document.getElementById("balDist");
    const bt = document.getElementById("balTime");
    const bs = document.getElementById("balShadePct");
    const bb = document.getElementById("balShadeBar");
    if (bd) bd.innerText = `${data.balanced.distance_m} m`;
    if (bt) bt.innerText = `${data.balanced.time_min} min`;
    if (bs) bs.innerText = `${data.balanced.shade_pct}%`;
    if (bb) bb.style.width = `${Math.min(100, data.balanced.shade_pct)}%`;
  } else if (balCard) {
    balCard.style.display = "none";
  }

  if (data.tradeoff) {
    const verdict = data.tradeoff.verdict || "Optimal shade path verified";
    const tv = document.getElementById("tradeoffVerdict");
    if (tv) tv.innerText = verdict;
    const dd = document.getElementById("deltaDist");
    const dt = document.getElementById("deltaTime");
    const ds = document.getElementById("deltaShade");
    if (dd) dd.innerText = `+${data.tradeoff.extra_distance_m} m`;
    if (dt) dt.innerText = `+${data.tradeoff.extra_time_min} min`;
    if (ds) ds.innerText = `+${data.tradeoff.shade_gain_pct}%`;
  }

  const therm = data.thermal || (data.coolest ? data.coolest.thermal : null);
  const rel = document.getElementById("thermalRelief");
  const av = document.getElementById("heatAvoided");
  if (therm) {
    if (rel) rel.innerText = `${therm.apparent_temp_relief_c || -3.6} °C`;
    if (av) av.innerText = `${therm.solar_heat_avoided_w || 420} W/m²`;
  }
}

function setupVirtualWalker(coolCoords) {
  const panel = document.getElementById("simulationPanel");
  if (!panel || !coolCoords || coolCoords.length === 0) return;
  panel.style.display = "";
  simCoords = coolCoords;
  resetSimulation();
}

function resetSimulation() {
  pauseSimulation();
  simIndex = 0;
  simElapsedSeconds = 0;
  updateSimHUD(0, 0, 0, "00:00");
  const pBar = document.getElementById("simProgressBar");
  if (pBar) pBar.style.width = "0%";
  const playBtn = document.getElementById("simPlayBtn");
  if (playBtn) playBtn.innerHTML = "▶ Start Walk";

  const banner = document.getElementById("gmapsNavBanner");
  if (banner) banner.style.display = "none";

  if (simCoords && simCoords.length > 0) {
    const startPt = simCoords[0];
    if (!walkerMarker) {
      const walkerIcon = L.divIcon({
        className: 'gmaps-nav-puck',
        html: '<div style="position:relative;width:32px;height:32px;display:flex;align-items:center;justify-content:center;"><div style="position:absolute;width:32px;height:32px;border-radius:50%;background:rgba(26,115,232,0.25);animation:gmapsPulse 1.5s infinite;"></div><div style="width:18px;height:18px;border-radius:50%;background:#1a73e8;border:3px solid #ffffff;box-shadow:0 2px 6px rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;"><div style="width:4px;height:4px;border-radius:50%;background:#ffffff;"></div></div></div>',
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });
      walkerMarker = L.marker(startPt, { icon: walkerIcon, zIndexOffset: 1000 }).addTo(map);
    } else {
      walkerMarker.setLatLng(startPt);
    }
  }
}

function startSimulation() {
  if (!simCoords || simCoords.length === 0) return;
  simIsPlaying = true;
  const playBtn = document.getElementById("simPlayBtn");
  if (playBtn) playBtn.innerHTML = "⏸ Pause Walk";

  const banner = document.getElementById("gmapsNavBanner");
  if (banner) banner.style.display = "flex";

  if (simInterval) clearInterval(simInterval);
  simInterval = setInterval(() => {
    if (simIndex >= simCoords.length - 1) {
      pauseSimulation();
      if (playBtn) playBtn.innerHTML = "✅ Walk Finished";
      return;
    }

    simIndex = Math.min(simCoords.length - 1, simIndex + simSpeed);
    const currPt = simCoords[simIndex];
    if (walkerMarker) walkerMarker.setLatLng(currPt);

    const pct = ((simIndex / (simCoords.length - 1)) * 100).toFixed(1);
    const pBar = document.getElementById("simProgressBar");
    if (pBar) pBar.style.width = `${pct}%`;

    const totalDist = currentRouteData && currentRouteData.coolest ? currentRouteData.coolest.distance_m : 2500;
    const walkedDist = Math.round((simIndex / (simCoords.length - 1)) * totalDist);
    simElapsedSeconds += (simSpeed * 1.5);
    const mins = Math.floor(simElapsedSeconds / 60);
    const secs = Math.floor(simElapsedSeconds % 60);
    const elapsedStr = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

    let instantShade = 65;
    let solarFlux = 620;
    let streetName = "Tree-shaded Avenue";
    if (currentRouteData && currentRouteData.steps && currentRouteData.steps.length > 0) {
      const stepIdx = Math.min(currentRouteData.steps.length - 1, Math.floor((simIndex / simCoords.length) * currentRouteData.steps.length));
      const curStep = currentRouteData.steps[stepIdx];
      instantShade = curStep.shade_pct || 65;
      solarFlux = curStep.solar_irradiance_w || 620;
      streetName = curStep.street || "Shaded Street";
    }

    updateSimHUD(walkedDist, instantShade, solarFlux, elapsedStr);

    const remMeters = Math.max(0, totalDist - walkedDist);
    const remMins = Math.ceil(remMeters / 80);
    const navMain = document.getElementById("navMainText");
    const navSub = document.getElementById("navSubText");
    const navRem = document.getElementById("navRemaining");
    if (navMain) navMain.innerText = `Walking on ${streetName}`;
    if (navSub) navSub.innerText = `${instantShade}% in Shade • Solar flux ${solarFlux} W/m²`;
    if (navRem) navRem.innerText = `${remMeters}m • ~${remMins} min`;
  }, 100);
}

function pauseSimulation() {
  simIsPlaying = false;
  if (simInterval) {
    clearInterval(simInterval);
    simInterval = null;
  }
  const playBtn = document.getElementById("simPlayBtn");
  if (playBtn) playBtn.innerHTML = "▶ Resume Walk";
}

function updateSimHUD(dist, shade, solar, timeStr) {
  const d = document.getElementById("hudDistance");
  const s = document.getElementById("hudShade");
  const f = document.getElementById("hudSolar");
  const t = document.getElementById("hudElapsed");
  if (d) d.innerText = `${dist} m`;
  if (s) s.innerText = `${shade}%`;
  if (f) f.innerText = `${solar} W/m²`;
  if (t) t.innerText = timeStr;
}

function renderHeatStrain(thermal) {
  const p = document.getElementById("heatStrainPanel");
  if (!p) return;
  p.style.display = "";

  const sr = document.getElementById("sweatRateVal");
  const wl = document.getElementById("waterLossVal");
  const ws = document.getElementById("waterSavedVal");
  const rs = document.getElementById("restStopsVal");
  const ha = document.getElementById("hydrationAdvice");

  if (thermal) {
    if (sr) sr.innerText = `${thermal.sweat_rate_ml_hr || 285} mL/h`;
    if (wl) wl.innerText = `${thermal.total_water_loss_ml || 90} mL`;
    if (ws) ws.innerText = `+${thermal.water_saved_ml || 34} mL`;
    if (rs) rs.innerText = `${thermal.canopy_rest_stops || 1} stop`;
    if (ha && thermal.hydration_advice) ha.innerText = thermal.hydration_advice;
  }
}

function renderTurnStepsExtended(steps) {
  const stepsList = document.getElementById("stepsList");
  const stepper = document.getElementById("stepStepperBtns");
  if (!stepsList) return;
  stepsList.innerHTML = "";
  if (!steps || steps.length === 0) {
    stepsList.innerHTML = '<div style="font-size:12px;color:#5f6368;padding:8px;">No steps available.</div>';
    if (stepper) stepper.style.display = "none";
    return;
  }
  if (stepper) stepper.style.display = "flex";
  currentStepIndex = 0;
  updateStepCounter(steps.length);

  steps.forEach((step, idx) => {
    const div = document.createElement("div");
    const isShaded = (step.shade_pct || (step.is_shaded ? 70 : 10)) >= 35;
    div.className = "step-card";
    div.innerHTML = `
      <div class="step-icon">${isShaded ? "🌳" : "☀️"}</div>
      <div style="flex:1;">
        <div class="step-street">${step.street} (${step.distance_m}m)</div>
        <div class="step-desc">${isShaded ? "Shaded corridor" : "Exposed sun"} • ${step.infrastructure || "Sidewalk"}</div>
        ${step.advisory ? `<div style="font-size:11px;color:#0F9D58;margin-top:2px;">💡 ${step.advisory}</div>` : ""}
      </div>
    `;
    div.addEventListener("click", () => focusStep(idx));
    stepsList.appendChild(div);
  });
}

function focusStep(idx) {
  const steps = currentRouteData ? (currentRouteData.steps || (currentRouteData.coolest && currentRouteData.coolest.steps)) : null;
  if (!steps || idx < 0 || idx >= steps.length) return;
  currentStepIndex = idx;
  updateStepCounter(steps.length);

  const coolCoords = extractCoords(currentRouteData.coolest);
  if (coolCoords && coolCoords.length > 0) {
    const ratio = idx / steps.length;
    const coordIdx = Math.min(coolCoords.length - 1, Math.floor(ratio * coolCoords.length));
    const pt = coolCoords[coordIdx];
    map.panTo(pt, { animate: true, duration: 0.4 });
  }
}

function updateStepCounter(total) {
  const c = document.getElementById("stepCounter");
  if (c) c.innerText = `${currentStepIndex + 1} / ${total}`;
}

function addToHistory(data) {
  const coolest = data.coolest || {};
  const startSelect = document.getElementById("startSelect");
  const destSelect = document.getElementById("destSelect");
  const startName = startSelect?.options[startSelect.selectedIndex]?.text || "Custom";
  const destName  = destSelect?.options[destSelect.selectedIndex]?.text  || "Custom";

  const entry = {
    from: startName,
    to:   destName,
    time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    hour: selectedHour,
    coolest_shade: coolest.shade_pct || 0,
    coolest_dist:  coolest.distance_m || 0
  };
  routeHistory.unshift(entry);
  if (routeHistory.length > 5) routeHistory.pop();
  renderHistory();
}

function renderHistory() {
  const list = document.getElementById("historyList");
  if (!list) return;
  if (routeHistory.length === 0) {
    list.innerHTML = '<div style="font-size:12px;color:#80868b;padding:4px;">No routes calculated yet.</div>';
    return;
  }
  list.innerHTML = routeHistory.map(e => `
    <div style="font-size:11.5px;padding:4px 0;border-bottom:1px solid #f1f3f4;display:flex;justify-content:space-between;">
      <span>${e.from} → ${e.to}</span>
      <span style="color:#0F9D58;font-weight:600;">${e.coolest_shade}% shade</span>
    </div>
  `).join("");
}

function setupEventListeners() {
  document.querySelectorAll(".gmaps-chip[data-from]").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".gmaps-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      const from = chip.getAttribute("data-from");
      const to   = chip.getAttribute("data-to");
      const s = document.getElementById("startSelect");
      const d = document.getElementById("destSelect");
      if (s) s.value = from;
      if (d) d.value = to;
      applyLandmarkSelection();
      calculateRoutes();
    });
  });

  const startSelect = document.getElementById("startSelect");
  const destSelect  = document.getElementById("destSelect");
  if (startSelect) startSelect.addEventListener("change", () => { applyLandmarkSelection(); calculateRoutes(); });
  if (destSelect) destSelect.addEventListener("change", () => { applyLandmarkSelection(); calculateRoutes(); });

  const swapBtn = document.getElementById("swapLocationsBtn");
  if (swapBtn) {
    swapBtn.addEventListener("click", () => {
      const sVal = startSelect.value;
      const dVal = destSelect.value;
      startSelect.value = dVal;
      destSelect.value  = sVal;
      applyLandmarkSelection();
      calculateRoutes();
    });
  }

  const findBtn = document.getElementById("findRoutesBtn");
  if (findBtn) findBtn.addEventListener("click", calculateRoutes);

  document.querySelectorAll(".gmaps-time-pill").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".gmaps-time-pill").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const h = btn.getAttribute("data-hour");
      if (h === "live") {
        selectedHour = new Date().getHours();
        document.getElementById("timeLabel").innerText = `Live Clock (${selectedHour}:00)`;
      } else {
        selectedHour = parseInt(h);
        document.getElementById("timeLabel").innerText = `${selectedHour}:00 (${selectedHour === 13 ? "Peak Heat" : selectedHour === 9 ? "Morning Sun" : "Afternoon Sun"})`;
      }
      calculateRoutes();
    });
  });

  const layerTrigger = document.getElementById("layerTriggerBtn");
  const layerPopover = document.getElementById("layerPopover");
  if (layerTrigger && layerPopover) {
    layerTrigger.addEventListener("click", (e) => {
      e.stopPropagation();
      const isVisible = layerPopover.style.display !== "none";
      layerPopover.style.display = isVisible ? "none" : "block";
    });
    document.addEventListener("click", () => { layerPopover.style.display = "none"; });
    layerPopover.addEventListener("click", (e) => e.stopPropagation());
  }

  document.querySelectorAll(".layer-option").forEach(opt => {
    opt.addEventListener("click", () => {
      const lyr = opt.getAttribute("data-layer");
      switchBasemap(lyr);
    });
  });

  const zoomIn = document.getElementById("zoomInBtn");
  const zoomOut = document.getElementById("zoomOutBtn");
  if (zoomIn) zoomIn.addEventListener("click", () => map.zoomIn());
  if (zoomOut) zoomOut.addEventListener("click", () => map.zoomOut());

  const recenter = document.getElementById("recenterBtn");
  if (recenter) {
    recenter.addEventListener("click", () => {
      const bounds = [[PILOT_BBOX[1], PILOT_BBOX[0]], [PILOT_BBOX[3], PILOT_BBOX[2]]];
      map.fitBounds(bounds, { padding: [50, 50] });
    });
  }

  const crosshair = document.getElementById("locateCrosshairBtn");
  const locateMe = document.getElementById("locateMeBtn");
  if (crosshair) crosshair.addEventListener("click", locateUserGPS);
  if (locateMe) locateMe.addEventListener("click", locateUserGPS);

  const togglePanel = document.getElementById("togglePanelBtn");
  const sidebar = document.getElementById("sidebar");
  if (togglePanel && sidebar) {
    togglePanel.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
      togglePanel.innerText = sidebar.classList.contains("collapsed") ? "▶" : "◀";
    });
  }

  const advToggle = document.getElementById("advancedToggle");
  const advPanel = document.getElementById("advancedPanel");
  if (advToggle && advPanel) {
    advToggle.addEventListener("click", () => {
      const isHidden = advPanel.style.display === "none";
      advPanel.style.display = isHidden ? "flex" : "none";
    });
  }

  const cCard = document.getElementById("coolestRouteCard");
  const bCard = document.getElementById("balancedCard");
  const fCard = document.getElementById("fastestRouteCard");
  if (cCard) cCard.addEventListener("click", () => highlightActiveRoute("coolest"));
  if (bCard) bCard.addEventListener("click", () => highlightActiveRoute("balanced"));
  if (fCard) fCard.addEventListener("click", () => highlightActiveRoute("fastest"));

  const startNavBtn = document.getElementById("startCoolNavBtn");
  if (startNavBtn) {
    startNavBtn.addEventListener("click", () => {
      highlightActiveRoute("coolest");
      startSimulation();
      const coolCoords = extractCoords(currentRouteData ? currentRouteData.coolest : null);
      if (coolCoords && coolCoords.length > 0) {
        map.setView(coolCoords[0], 17, { animate: true });
      }
    });
  }

  const navClose = document.getElementById("navCloseBtn");
  if (navClose) {
    navClose.addEventListener("click", () => {
      pauseSimulation();
      const banner = document.getElementById("gmapsNavBanner");
      if (banner) banner.style.display = "none";
    });
  }

  const previewSteps = document.getElementById("previewCoolStepsBtn");
  if (previewSteps) {
    previewSteps.addEventListener("click", () => {
      const stepsDiv = document.getElementById("stepsList");
      if (stepsDiv) stepsDiv.scrollIntoView({ behavior: "smooth" });
    });
  }

  const exportGpx = document.getElementById("exportGpxBtn");
  if (exportGpx) exportGpx.addEventListener("click", downloadRouteGPX);

  const exportGeo = document.getElementById("exportGeoJsonBtn");
  if (exportGeo) {
    exportGeo.addEventListener("click", () => {
      if (!currentRouteData) { alert("Please calculate a route first."); return; }
      const str = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentRouteData, null, 2));
      const a = document.createElement("a");
      a.setAttribute("href", str);
      a.setAttribute("download", `pune_cooler_routes_${Date.now()}.geojson`);
      document.body.appendChild(a);
      a.click();
      a.remove();
    });
  }

  const resetPins = document.getElementById("resetPinsBtn");
  if (resetPins) {
    resetPins.addEventListener("click", () => {
      if (startMarker) { map.removeLayer(startMarker); startMarker = null; }
      if (destMarker) { map.removeLayer(destMarker); destMarker = null; }
      clearRouteLayers();
      const resultsSec = document.getElementById("resultsSection");
      if (resultsSec) resultsSec.style.display = "none";
    });
  }

  const shareBtn = document.getElementById("shareRouteBtn");
  if (shareBtn) shareBtn.addEventListener("click", shareRouteURL);

  const heatToggle = document.getElementById("heatmapToggle");
  if (heatToggle) heatToggle.addEventListener("change", toggleHeatmap);

  const isoToggle = document.getElementById("isochroneToggle");
  if (isoToggle) isoToggle.addEventListener("change", toggleIsochrone);
}

const _originalCalcRoutes = calculateRoutes;
calculateRoutes = async function() {
  await _originalCalcRoutes.apply(this, arguments);
  if (currentRouteData) {
    const coolCoords = extractCoords(currentRouteData.coolest);
    setupVirtualWalker(coolCoords);
    renderHeatStrain(currentRouteData.thermal);
    renderTurnStepsExtended(currentRouteData.steps || (currentRouteData.coolest ? currentRouteData.coolest.steps : []));
  }
};

function locateUserGPS() {
  if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser.");
    return;
  }
  const btn = document.getElementById("locateMeBtn");
  if (btn) btn.innerText = "Locating GPS...";

  navigator.geolocation.getCurrentPosition(
    pos => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      setStartMarker(lat, lon, "My GPS Location");
      map.setView([lat, lon], 16);
      if (btn) btn.innerText = "✅ GPS Located!";
      setTimeout(() => { if (btn) btn.innerText = "Your location"; }, 2500);
      calculateRoutes();
    },
    err => {
      console.warn("GPS error fallback:", err);
      setStartMarker(18.5178, 73.8151, "MIT-WPU Campus (Center)");
      if (btn) btn.innerText = "Your location";
      calculateRoutes();
    },
    { enableHighAccuracy: true, timeout: 6000 }
  );
}

function downloadRouteGPX() {
  if (!currentRouteData || !currentRouteData.coolest) {
    alert("Please calculate a route first before downloading GPX.");
    return;
  }
  const coolCoords = extractCoords(currentRouteData.coolest);
  if (!coolCoords || coolCoords.length === 0) return;

  let gpx = '<?xml version="1.0" encoding="UTF-8"?>\n' +
            '<gpx version="1.1" creator="PuneCoolerRoutes" xmlns="http://www.topografix.com/GPX/1/1">\n' +
            '  <metadata><name>Pune_Cooler_Route</name></metadata>\n' +
            '  <trk><name>Coolest Shaded Route</name><trkseg>\n';
  coolCoords.forEach(pt => {
    gpx += `    <trkpt lat="${pt[0].toFixed(6)}" lon="${pt[1].toFixed(6)}"/>\n`;
  });
  gpx += '  </trkseg></trk>\n</gpx>';

  const blob = new Blob([gpx], { type: "application/x-gpx+xml" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `pune_cool_route_${Date.now()}.gpx`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function shareRouteURL() {
  if (!startMarker || !destMarker) return;
  const s = startMarker.getLatLng();
  const d = destMarker.getLatLng();
  const url = `${window.location.origin}/#from=${s.lat.toFixed(4)},${s.lng.toFixed(4)}&to=${d.lat.toFixed(4)},${d.lng.toFixed(4)}&hour=${selectedHour}`;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(url).then(() => alert("Route link copied to clipboard!"));
  } else {
    prompt("Copy route link:", url);
  }
}

function toggleHeatmap() {
  if (heatmapActive) {
    if (heatmapLayer) { map.removeLayer(heatmapLayer); heatmapLayer = null; }
    heatmapActive = false;
  } else {
    fetch("/outputs/day8_heatmap.geojson")
      .then(r => r.json())
      .then(data => {
        const slot = selectedHour < 11 ? "shade_0900" : selectedHour < 15 ? "shade_1300" : "shade_1600";
        heatmapLayer = L.geoJSON(data, {
          style: feature => {
            const shade = feature.properties[slot] || feature.properties.composite || 0;
            return { color: shade >= 0.5 ? "#0F9D58" : shade >= 0.3 ? "#fbbc04" : "#ea4335", weight: 3, opacity: 0.8 };
          }
        }).addTo(map);
        heatmapActive = true;
      }).catch(err => console.warn(err));
  }
}

function toggleIsochrone() {
  if (isochroneActive) {
    if (isochroneLayerShd) { map.removeLayer(isochroneLayerShd); isochroneLayerShd = null; }
    isochroneActive = false;
  } else {
    fetch("/outputs/day8_isochrone_shaded.geojson")
      .then(r => r.json())
      .then(shadedData => {
        isochroneLayerShd = L.geoJSON(shadedData, {
          style: { color: "#0F9D58", weight: 2, opacity: 0.7, fillOpacity: 0.1, dashArray: "6, 4" }
        }).addTo(map);
        isochroneActive = true;
      }).catch(err => console.warn(err));
  }
}

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  }
}
