/**
 * Pune Cooler Routes - Interactive Map Application Logic
 */

// Global State
let map;
let landmarks = {};
let startMarker = null;
let destMarker = null;
let fastestPolyline = null;
let coolestPolyline = null;
let boundaryPolygon = null;
let currentRouteData = null;

let selectedHour = 13;
let selectedCoolness = 2.5;

// Pilot Bounding Box (west, south, east, north)
const PILOT_BBOX = [73.802, 18.495, 73.846, 18.531];

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  loadLandmarks();
  setupEventListeners();
});

/**
 * Initialize Leaflet Map
 */
function initMap() {
  const centerLat = (PILOT_BBOX[1] + PILOT_BBOX[3]) / 2;
  const centerLon = (PILOT_BBOX[0] + PILOT_BBOX[2]) / 2;

  map = L.map("map", {
    center: [centerLat, centerLon],
    zoom: 14,
    zoomControl: true
  });

  // Dark Theme Tiles (CartoDB Dark Matter)
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 19
  }).addTo(map);

  // Draw Pilot Bounding Box
  const bounds = [
    [PILOT_BBOX[1], PILOT_BBOX[0]], // South-West
    [PILOT_BBOX[3], PILOT_BBOX[2]]  // North-East
  ];

  boundaryPolygon = L.rectangle(bounds, {
    color: "#f59e0b",
    weight: 2,
    dashArray: "6, 6",
    fillColor: "#f59e0b",
    fillOpacity: 0.05
  }).addTo(map);

  // Map Click Listener to drop custom pins
  map.on("click", onMapClick);
}

/**
 * Handle Map Clicks for Origin & Destination
 */
function onMapClick(e) {
  const { lat, lng } = e.latlng;

  // Check if click is inside pilot box
  if (
    lng < PILOT_BBOX[0] ||
    lng > PILOT_BBOX[2] ||
    lat < PILOT_BBOX[1] ||
    lat > PILOT_BBOX[3]
  ) {
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
    // Both already exist: reset and make this the new start
    setStartMarker(lat, lng, "Custom Start");
    if (destMarker) {
      map.removeLayer(destMarker);
      destMarker = null;
    }
    clearRouteLayers();
  }
}

/**
 * Set Start Marker
 */
function setStartMarker(lat, lng, title = "Origin") {
  if (startMarker) map.removeLayer(startMarker);

  const startIcon = L.divIcon({
    className: "custom-marker-start",
    html: `<div style="background-color:#10b981; width:16px; height:16px; border-radius:50%; border:3px solid #ffffff; box-shadow:0 0 10px #10b981;"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });

  startMarker = L.marker([lat, lng], { icon: startIcon, draggable: true })
    .addTo(map)
    .bindPopup(`<b>Start:</b> ${title}`);

  startMarker.on("dragend", () => calculateRoutes());
}

/**
 * Set Destination Marker
 */
function setDestMarker(lat, lng, title = "Destination") {
  if (destMarker) map.removeLayer(destMarker);

  const destIcon = L.divIcon({
    className: "custom-marker-dest",
    html: `<div style="background-color:#ef4444; width:16px; height:16px; border-radius:50%; border:3px solid #ffffff; box-shadow:0 0 10px #ef4444;"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });

  destMarker = L.marker([lat, lng], { icon: destIcon, draggable: true })
    .addTo(map)
    .bindPopup(`<b>Destination:</b> ${title}`);

  destMarker.on("dragend", () => calculateRoutes());
}

/**
 * Fetch Landmarks from Backend
 */
async function loadLandmarks() {
  try {
    const res = await fetch("/api/landmarks");
    if (!res.ok) throw new Error("Failed to fetch landmarks");
    landmarks = await res.json();

    const startSelect = document.getElementById("startSelect");
    const destSelect = document.getElementById("destSelect");

    startSelect.innerHTML = `<option value="custom">📍 Custom Map Pin</option>`;
    destSelect.innerHTML = `<option value="custom">📍 Custom Map Pin</option>`;

    for (const [key, item] of Object.entries(landmarks)) {
      startSelect.innerHTML += `<option value="${key}">${item.name}</option>`;
      destSelect.innerHTML += `<option value="${key}">${item.name}</option>`;
    }

    // Default: MIT-WPU to Fergusson College
    startSelect.value = "mit_wpu";
    destSelect.value = "fergusson";

    applyLandmarkSelection();
    calculateRoutes();
  } catch (err) {
    console.error("Error loading landmarks:", err);
  }
}

/**
 * Apply Landmark Selection from Dropdowns
 */
function applyLandmarkSelection() {
  const startKey = document.getElementById("startSelect").value;
  const destKey = document.getElementById("destSelect").value;

  if (startKey && landmarks[startKey]) {
    const lm = landmarks[startKey];
    setStartMarker(lm.lat, lm.lon, lm.name);
  }
  if (destKey && landmarks[destKey]) {
    const lm = landmarks[destKey];
    setDestMarker(lm.lat, lm.lon, lm.name);
  }
}

/**
 * Calculate Dual Routes via Backend API
 */
async function calculateRoutes() {
  if (!startMarker || !destMarker) return;

  const startLatLng = startMarker.getLatLng();
  const destLatLng = destMarker.getLatLng();

  const btn = document.getElementById("findRoutesBtn");
  btn.innerHTML = `<span class="btn-icon">⏳</span> Computing...`;
  btn.disabled = true;

  const url = `/api/route?start_lat=${startLatLng.lat}&start_lon=${startLatLng.lng}&dest_lat=${destLatLng.lat}&dest_lon=${destLatLng.lng}&hour=${selectedHour}&coolness=${selectedCoolness}`;

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
    btn.innerHTML = `<span class="btn-icon">⚡</span> Calculate Dual Routes`;
    btn.disabled = false;
  }
}

/**
 * Render Route Polylines on Leaflet Map
 */
function renderRoutesOnMap(data) {
  clearRouteLayers();

  const fastestCoords = data.fastest.coordinates;
  const coolestCoords = data.coolest.coordinates;

  // Fastest Route (Cyan Line)
  fastestPolyline = L.polyline(fastestCoords, {
    color: "#06b6d4",
    weight: 5,
    opacity: 0.85,
    dashArray: "8, 6",
    lineJoin: "round"
  }).addTo(map);

  fastestPolyline.bindPopup(`
    <b>⚡ Fastest Walking Route</b><br>
    Distance: ${data.fastest.distance_m} m<br>
    Time: ${data.fastest.time_min} min<br>
    Shade: ${data.fastest.shade_pct}%
  `);

  // Coolest Route (Emerald Glow Line)
  coolestPolyline = L.polyline(coolestCoords, {
    color: "#10b981",
    weight: 6,
    opacity: 0.95,
    lineJoin: "round"
  }).addTo(map);

  coolestPolyline.bindPopup(`
    <b>🌿 Coolest Shaded Route</b><br>
    Distance: ${data.coolest.distance_m} m<br>
    Time: ${data.coolest.time_min} min<br>
    Shade: ${data.coolest.shade_pct}% (Maximized Tree/Building Shade)
  `);

  // Fit bounds to show both routes comfortably
  const group = new L.featureGroup([fastestPolyline, coolestPolyline]);
  map.fitBounds(group.getBounds(), { padding: [50, 50] });
}

/**
 * Clear existing polylines
 */
function clearRouteLayers() {
  if (fastestPolyline) {
    map.removeLayer(fastestPolyline);
    fastestPolyline = null;
  }
  if (coolestPolyline) {
    map.removeLayer(coolestPolyline);
    coolestPolyline = null;
  }
}

/**
 * Render Comparison Metrics in DOM
 */
function renderMetrics(data) {
  // Tradeoff Verdict Banner
  document.getElementById("tradeoffVerdict").innerText = data.tradeoff.verdict;

  // Fastest Card
  document.getElementById("fastDist").innerText = `${data.fastest.distance_m} m`;
  document.getElementById("fastTime").innerText = `${data.fastest.time_min} min`;
  document.getElementById("fastShadePct").innerText = `${data.fastest.shade_pct}%`;
  document.getElementById("fastShadeBar").style.width = `${Math.min(100, data.fastest.shade_pct)}%`;

  // Coolest Card
  document.getElementById("coolDist").innerText = `${data.coolest.distance_m} m`;
  document.getElementById("coolTime").innerText = `${data.coolest.time_min} min`;
  document.getElementById("coolShadePct").innerText = `${data.coolest.shade_pct}%`;
  document.getElementById("coolShadeBar").style.width = `${Math.min(100, data.coolest.shade_pct)}%`;

  // Delta Chips
  document.getElementById("deltaDist").innerText = `+${data.tradeoff.extra_distance_m} m`;
  document.getElementById("deltaTime").innerText = `+${data.tradeoff.extra_time_min} min`;
  document.getElementById("deltaShade").innerText = `+${data.tradeoff.shade_gain_pct}%`;

  // Turn-by-Turn Steps
  const stepsList = document.getElementById("stepsList");
  stepsList.innerHTML = "";

  (data.coolest.steps || []).forEach(step => {
    const div = document.createElement("div");
    div.className = `step-item ${step.is_shaded ? "shaded" : ""}`;
    div.innerHTML = `
      <div class="step-street">${step.is_shaded ? "🌳" : "☀️"} ${step.street}</div>
      <div class="step-meta">
        <span>${step.length_m} m</span>
        <strong>${step.shade_pct}% shade</strong>
      </div>
    `;
    stepsList.appendChild(div);
  });
}

/**
 * Setup Event Listeners
 */
function setupEventListeners() {
  // Preset Chips
  document.querySelectorAll(".preset-chips .chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".preset-chips .chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");

      const fromKey = chip.getAttribute("data-from");
      const toKey = chip.getAttribute("data-to");

      document.getElementById("startSelect").value = fromKey;
      document.getElementById("destSelect").value = toKey;

      applyLandmarkSelection();
      calculateRoutes();
    });
  });

  // Dropdown Changes
  document.getElementById("startSelect").addEventListener("change", () => {
    applyLandmarkSelection();
    calculateRoutes();
  });
  document.getElementById("destSelect").addEventListener("change", () => {
    applyLandmarkSelection();
    calculateRoutes();
  });

  // Swap Locations Button
  document.getElementById("swapLocationsBtn").addEventListener("click", () => {
    const startSelect = document.getElementById("startSelect");
    const destSelect = document.getElementById("destSelect");
    const tempVal = startSelect.value;
    startSelect.value = destSelect.value;
    destSelect.value = tempVal;

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
        const labels = {
          9: "09:00 (Morning Sun)",
          13: "13:00 (Midday Sun)",
          16: "16:00 (Afternoon Sun)"
        };
        document.getElementById("timeLabel").innerText = labels[selectedHour] || `${selectedHour}:00`;
      }
      calculateRoutes();
    });
  });

  // Coolness Slider
  const coolnessSlider = document.getElementById("coolnessSlider");
  coolnessSlider.addEventListener("input", e => {
    selectedCoolness = parseFloat(e.target.value);
    document.getElementById("coolnessVal").innerText = `${selectedCoolness}x`;
  });
  coolnessSlider.addEventListener("change", () => {
    calculateRoutes();
  });

  // Calculate Button
  document.getElementById("findRoutesBtn").addEventListener("click", () => {
    calculateRoutes();
  });

  // Toggle Steps Accordion
  document.getElementById("toggleStepsBtn").addEventListener("click", () => {
    const list = document.getElementById("stepsList");
    const arrow = document.querySelector(".accordion-arrow");
    if (list.style.display === "none") {
      list.style.display = "flex";
      arrow.innerText = "▼";
    } else {
      list.style.display = "none";
      arrow.innerText = "▶";
    }
  });

  // Export GeoJSON Button
  document.getElementById("exportGeoJsonBtn").addEventListener("click", () => {
    if (!currentRouteData) {
      alert("Please calculate routes first.");
      return;
    }

    const geojson = {
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          properties: {
            route_type: "Fastest",
            distance_m: currentRouteData.fastest.distance_m,
            time_min: currentRouteData.fastest.time_min,
            shade_pct: currentRouteData.fastest.shade_pct
          },
          geometry: {
            type: "LineString",
            coordinates: currentRouteData.fastest.geojson_coords
          }
        },
        {
          type: "Feature",
          properties: {
            route_type: "Coolest",
            distance_m: currentRouteData.coolest.distance_m,
            time_min: currentRouteData.coolest.time_min,
            shade_pct: currentRouteData.coolest.shade_pct
          },
          geometry: {
            type: "LineString",
            coordinates: currentRouteData.coolest.geojson_coords
          }
        }
      ]
    };

    const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `pune_cooler_routes_${selectedHour}00.geojson`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // Reset Pins Button
  document.getElementById("resetPinsBtn").addEventListener("click", () => {
    if (startMarker) map.removeLayer(startMarker);
    if (destMarker) map.removeLayer(destMarker);
    startMarker = null;
    destMarker = null;
    clearRouteLayers();
    document.getElementById("startSelect").value = "custom";
    document.getElementById("destSelect").value = "custom";
    alert("Pins cleared! Click anywhere in the orange pilot box to set a new Start pin.");
  });
}
