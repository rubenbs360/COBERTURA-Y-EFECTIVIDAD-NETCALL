// Global State
let summaryData = null;
let departmentsData = [];
let storesData = [];
let advisorsData = [];
let coberturaData = null;

let selectedStoreId = null;
let currentTab = "tab-map";
let map = null;
let tileLayer = null;
let geoJsonLayer = null;
let storeMarkersLayer = null;

// Department coordinates mapping for map zooming
const deptCoordinates = {
  "lima - callao": { lat: -12.0463, lng: -77.0427, zoom: 10 },
  "piura": { lat: -5.1944, lng: -80.6328, zoom: 9 },
  "tumbes": { lat: -3.5669, lng: -80.4515, zoom: 10 },
  "lambayeque": { lat: -6.7011, lng: -79.9061, zoom: 9 },
  "la libertad": { lat: -8.1159, lng: -79.0289, zoom: 10 },
  "arequipa": { lat: -16.4090, lng: -71.5375, zoom: 10 },
  "junin": { lat: -11.1582, lng: -75.9930, zoom: 8 },
  "ica": { lat: -14.0678, lng: -75.7286, zoom: 10 },
  "ancash": { lat: -9.5261, lng: -77.5288, zoom: 9 },
  "puno": { lat: -15.8402, lng: -70.0219, zoom: 9 },
  "cusco": { lat: -13.5319, lng: -71.9675, zoom: 10 },
  "todos": { lat: -9.19, lng: -75.01, zoom: 6 }
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  setupTabListeners();
  setupThemeToggler();
  setupAdminListeners();
  setupCoordinateSearch();
  setupTemplateButtons();
  loadData();
});

// Fetch data from processed JSON files
async function loadData() {
  try {
    const [summaryRes, deptsRes, storesRes, advisorsRes, coberturaRes] = await Promise.all([
      fetch("data/summary.json"),
      fetch("data/departments.json"),
      fetch("data/stores.json"),
      fetch("data/advisors.json"),
      fetch("data/cobertura.json")
    ]);

    summaryData = await summaryRes.json();
    departmentsData = await deptsRes.json();
    storesData = await storesRes.json();
    advisorsData = await advisorsRes.json();
    coberturaData = await coberturaRes.json();

    // Populate UI elements
    populateDeptSelect();
    initMap();
    updateRegionalPerformance();
    renderStoresList();
    
    // Set update time in header
    document.getElementById("header-update-time").textContent = new Date().toLocaleDateString('es-PE', {
      day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });

  } catch (error) {
    console.error("Error loading JSON data:", error);
    // Render fallback data warnings
    const container = document.getElementById("stores-list-container");
    if (container) {
      container.innerHTML = `<div class="loading-spinner text-danger">Error al cargar la base de datos local. Por favor, procese los archivos en Administración.</div>`;
    }
  }
}

// Navigation & Tab Switching
function setupTabListeners() {
  const navItems = document.querySelectorAll(".nav-item");
  const tabViews = document.querySelectorAll(".tab-view");

  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const targetTab = item.getAttribute("data-tab");
      
      navItems.forEach(nav => nav.classList.remove("active"));
      tabViews.forEach(view => view.classList.remove("active-view"));
      
      item.classList.add("active");
      document.getElementById(targetTab).classList.add("active-view");
      
      currentTab = targetTab;
      
      // Leaflet needs recalculation of size when shown from display: none
      if (currentTab === "tab-map" && map) {
        setTimeout(() => {
          map.invalidateSize();
        }, 100);
      }
    });
  });
}

// Dark/Light Theme Switching
function setupThemeToggler() {
  const toggleBtn = document.getElementById("theme-toggle");
  if (!toggleBtn) return;
  
  toggleBtn.addEventListener("click", () => {
    const isDark = document.body.classList.contains("dark-theme");
    if (isDark) {
      document.body.classList.remove("dark-theme");
      document.body.classList.add("light-theme");
      toggleBtn.innerHTML = '<span class="btn-icon">🌙</span> <span class="btn-lbl">Tema Oscuro</span>';
      
      // Update tile layer if map initialized
      if (map && tileLayer) {
        map.removeLayer(tileLayer);
        tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
          attribution: '&copy; CartoDB'
        }).addTo(map);
      }
    } else {
      document.body.classList.remove("light-theme");
      document.body.classList.add("dark-theme");
      toggleBtn.innerHTML = '<span class="btn-icon">☀️</span> <span class="btn-lbl">Tema Claro</span>';
      
      // Update tile layer if map initialized
      if (map && tileLayer) {
        map.removeLayer(tileLayer);
        tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
          attribution: '&copy; CartoDB'
        }).addTo(map);
      }
    }
  });
}

// Map Initialization and Rendering
function initMap() {
  if (map) return; // Already initialized

  // Center in Peru
  map = L.map('map').setView([-9.19, -75.01], 6);

  // Set CartoDB voyager as default tile layer (Light Theme)
  tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; CartoDB'
  }).addTo(map);

  // Layer groups for markers
  storeMarkersLayer = L.layerGroup().addTo(map);

  // Load GeoJSON Polygons
  if (coberturaData) {
    renderPolygons();
  }

  // Draw Store Markers on map
  updateMapMarkers();

  // Setup listeners for controls
  document.getElementById("map-dept-select").addEventListener("change", handleMapFiltersChange);
  document.querySelectorAll('input[name="despacho-tipo"]').forEach(radio => {
    radio.addEventListener("change", handleMapFiltersChange);
  });
}

// Render GeoJSON Polygons with proper styles and popups
function renderPolygons() {
  if (!coberturaData) return;

  geoJsonLayer = L.geoJSON(coberturaData, {
    style: function (feature) {
      const isNoColor = feature.properties.no_color === true;
      return {
        fillColor: isNoColor ? 'transparent' : (feature.properties.color_default || '#00ffff'),
        weight: 2,
        opacity: 0.8,
        color: isNoColor ? '#000000' : (feature.properties.color_default || '#00ffff'),
        fillOpacity: isNoColor ? 0.0 : 0.35
      };
    },
    onEachFeature: function (feature, layer) {
      // Hover effects
      layer.on('mouseover', function () {
        layer.setStyle({ fillOpacity: 0.65, weight: 3 });
      });
      layer.on('mouseout', function () {
        layer.setStyle({ fillOpacity: 0.35, weight: 2 });
      });

      // Bind interactive popup
      layer.on('click', function (e) {
        const props = feature.properties;
        const deptName = props.distrito || props.departamento;
        
        // Update district filter dropdown
        const matchedDistrict = findMatchingDistrictOption(deptName);
        if (matchedDistrict) {
          const select = document.getElementById("map-dept-select");
          if (select && select.value !== matchedDistrict) {
            select.value = matchedDistrict;
            handleMapFiltersChange();
          }
        }
        
        // Find current effectiveness for this department from stats
        const deptStat = departmentsData.find(d => d.departamento.toLowerCase() === deptName.toLowerCase());
        const effPercent = deptStat ? `${deptStat.effectiveness}%` : "No disponible";
        const ordersTotal = deptStat ? deptStat.total : 0;
        
        // Create speech text
        const speechText = `Estimado cliente, le confirmo que tenemos cobertura en la zona de ${props.nombre_comercial} (${props.distrito}). El despacho para esta zona es de tipo ${props.tipo_rango} con un horario de ${props.horario_cobertura}.`;

        const popupContent = `
          <div class="map-popup-container">
            <div class="map-popup-header">📍 ${props.nombre_comercial}</div>
            <div class="map-popup-row">
              <span class="map-popup-lbl">Distrito:</span>
              <span class="map-popup-val">${props.distrito} (${props.provincia})</span>
            </div>
            <div class="map-popup-row">
              <span class="map-popup-lbl">Rango Cobertura:</span>
              <span class="map-popup-val highlight">${props.tipo_rango}</span>
            </div>
            <div class="map-popup-row">
              <span class="map-popup-lbl">Horario de Atención:</span>
              <span class="map-popup-val">${props.horario_cobertura}</span>
            </div>
            <div class="map-popup-row" style="border-top: 1px solid var(--border-color); padding-top:0.3rem; margin-top:0.25rem;">
              <span class="map-popup-lbl">Efectividad ${deptName}:</span>
              <span class="map-popup-val text-success">${effPercent}</span>
            </div>
            <div class="map-popup-row">
              <span class="map-popup-lbl">Pedidos del Mes:</span>
              <span class="map-popup-val">${ordersTotal}</span>
            </div>
          </div>
        `;
        
        layer.bindPopup(popupContent).openPopup();
      });
    }
  }).addTo(map);
}

// Render store markers on the map
function updateMapMarkers() {
  if (!map || !storeMarkersLayer) return;
  
  storeMarkersLayer.clearLayers();
  
  const selectedDept = document.getElementById("map-dept-select").value.toLowerCase();
  
  storesData.forEach(store => {
    // Check if coordinates exist and matches department filter
    if (store.latitud && store.longitud) {
      if (selectedDept !== "todos" && store.distrito.toLowerCase() !== selectedDept) {
        return;
      }
      
      // Skip stores with no orders generated (Effectiveness: N/A)
      if (store.metricas.effectiveness === null) {
        return;
      }
      
      const markerColor = getEffectivenessColorClass(store.metricas.effectiveness);
      const iconHtml = `<div class="store-map-marker bg-${markerColor}">${store.pickup === 'SI' ? '📦' : '🏪'}</div>`;
      
      const customIcon = L.divIcon({
        className: 'custom-div-icon',
        html: iconHtml,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      });

      const markerPopup = `
        <div class="map-popup-container">
          <div class="map-popup-header">🏪 ${store.nombre}</div>
          <div class="map-popup-row">
            <span class="map-popup-lbl">ID PDV:</span>
            <span class="map-popup-val">${store.id_pdv}</span>
          </div>
          <div class="map-popup-row">
            <span class="map-popup-lbl">Canal:</span>
            <span class="map-popup-val">${store.canal} | ${store.subcanal}</span>
          </div>
          <div class="map-popup-row">
            <span class="map-popup-lbl">PickUp:</span>
            <span class="map-popup-val">${store.pickup}</span>
          </div>
          <div class="map-popup-row">
            <span class="map-popup-lbl">Efectividad Delivery:</span>
            <span class="map-popup-val ${markerColor}">${store.metricas.effectiveness !== null ? store.metricas.effectiveness + '%' : 'N/A'}</span>
          </div>
          <button class="map-popup-btn" style="background:var(--accent-purple); color:#fff;" onclick="viewStoreDetail(${store.id_pdv})">
            🔍 Ver Detalles y Nómina
          </button>
        </div>
      `;

      L.marker([store.latitud, store.longitud], { icon: customIcon })
        .bindPopup(markerPopup)
        .addTo(storeMarkersLayer);
    }
  });
}

// Populate the District select element in Map Controls
function populateDeptSelect() {
  const select = document.getElementById("map-dept-select");
  
  // Clear other options
  select.innerHTML = '<option value="todos">Todos los Distritos</option>';
  
  // Extract unique districts from data and sort
  const depts = departmentsData.map(d => d.departamento)
    .filter(d => d && d !== "No especificado")
    .sort((a, b) => a.localeCompare(b));
    
  depts.forEach(dept => {
    const opt = document.createElement("option");
    opt.value = dept;
    opt.textContent = dept;
    select.appendChild(opt);
  });
}

// Handle Map control changes
function handleMapFiltersChange(skipFlyTo = false) {
  updateRegionalPerformance();
  updateMapMarkers();
  
  if (skipFlyTo) return;
  
  // Smooth pan & Zoom to selected department coordinates
  const selectVal = document.getElementById("map-dept-select").value.toLowerCase();
  const coord = deptCoordinates[selectVal] || (selectVal === "todos" ? deptCoordinates["todos"] : null);
  if (!coord) return;
  
  map.flyTo([coord.lat, coord.lng], coord.zoom, {
    animate: true,
    duration: 1.5
  });
}

// Update performance sidebar details on Map tab
function updateRegionalPerformance() {
  const selectedDept = document.getElementById("map-dept-select").value;
  const selectedType = document.querySelector('input[name="despacho-tipo"]:checked').value;
  
  let total = 0;
  let delivered = 0;
  let failed = 0;
  let eff = 0.0;
  
  if (selectedDept === "todos") {
    // Sum all departments for selected dispatch type
    departmentsData.forEach(dept => {
      if (dept.dispatch && dept.dispatch[selectedType]) {
        const dInfo = dept.dispatch[selectedType];
        total += dInfo.total;
        delivered += dInfo.delivered;
        failed += (dInfo.anulado + dInfo.cancelado);
      }
    });
    
    document.getElementById("perf-dept-name").textContent = "Todo el País";
  } else {
    // Find matching department
    const dept = departmentsData.find(d => d.departamento.toLowerCase() === selectedDept.toLowerCase());
    if (dept) {
      if (dept.dispatch && dept.dispatch[selectedType]) {
        const dInfo = dept.dispatch[selectedType];
        total = dInfo.total;
        delivered = dInfo.delivered;
        failed = dInfo.anulado + dInfo.cancelado;
      } else {
        total = 0;
        delivered = 0;
        failed = 0;
      }
      document.getElementById("perf-dept-name").textContent = dept.departamento;
    } else {
      document.getElementById("perf-dept-name").textContent = selectedDept;
    }
  }

  // Calculate local effectiveness
  const denom = delivered + failed;
  eff = denom > 0 ? (delivered / denom * 100) : 0.0;

  // Render metrics
  document.getElementById("perf-eff-val").textContent = `${eff.toFixed(1)}%`;
  document.getElementById("perf-progress-bar").style.width = `${eff}%`;
  document.getElementById("perf-delivered").textContent = delivered.toLocaleString();
  document.getElementById("perf-failed").textContent = failed.toLocaleString();
}

// ================= STORES TAB LOGIC =================
// Render store list on left panel with filters
function renderStoresList() {
  const container = document.getElementById("stores-list-container");
  const searchQuery = document.getElementById("store-search-input").value.toLowerCase().trim();
  
  // Get active subcanal checkboxes
  const activeSubcanales = Array.from(document.querySelectorAll(".subcanal-filter:checked"))
    .map(cb => cb.value);

  container.innerHTML = "";

  // Filter stores data
  const filtered = storesData.filter(store => {
    // Subcanal filter
    if (!activeSubcanales.includes(store.subcanal)) {
      return false;
    }
    
    // Skip stores with no orders generated (Effectiveness: N/A)
    if (store.metricas.effectiveness === null) {
      return false;
    }

    // Search query filter (matches ID, name, department, provincia)
    if (searchQuery) {
      const matchId = store.id_pdv.toString().includes(searchQuery);
      const matchName = store.nombre.toLowerCase().includes(searchQuery);
      const matchDept = store.departamento.toLowerCase().includes(searchQuery);
      const matchProv = store.provincia.toLowerCase().includes(searchQuery);
      
      return matchId || matchName || matchDept || matchProv;
    }
    
    return true;
  });

  // Sort by ID or name
  filtered.sort((a, b) => a.nombre.localeCompare(b.nombre));

  if (filtered.length === 0) {
    container.innerHTML = `<div class="loading-spinner">No se encontraron tiendas matching.</div>`;
    return;
  }

  filtered.forEach(store => {
    const eff = store.metricas.effectiveness;
    const colorClass = getEffectivenessColorClass(eff);
    const effDisplay = eff !== null ? `${eff}%` : "N/A";
    
    const itemCard = document.createElement("div");
    itemCard.className = `store-item-card ${selectedStoreId === store.id_pdv ? 'selected' : ''}`;
    itemCard.setAttribute("data-id", store.id_pdv);
    
    itemCard.innerHTML = `
      <div class="store-item-info">
        <span class="store-item-id-badge">ID: ${store.id_pdv} • ${store.subcanal}</span>
        <span class="store-item-title">${store.nombre}</span>
        <span class="store-item-loc">📍 ${store.provincia || store.departamento}</span>
      </div>
      <div class="store-item-metric">
        <span class="store-item-eff-label">Efectividad</span>
        <span class="store-item-eff-val ${colorClass}">${effDisplay}</span>
      </div>
    `;

    itemCard.addEventListener("click", () => {
      selectStore(store.id_pdv);
    });

    container.appendChild(itemCard);
  });
}

// Select a store and display details on the right panel
function selectStore(storeId) {
  selectedStoreId = storeId;
  
  // Highlight selected item in list
  document.querySelectorAll(".store-item-card").forEach(card => {
    if (parseInt(card.getAttribute("data-id")) === storeId) {
      card.classList.add("selected");
    } else {
      card.classList.remove("selected");
    }
  });

  const store = storesData.find(s => s.id_pdv === storeId);
  if (!store) return;

  // Show detail content panel
  document.getElementById("store-detail-panel").querySelector(".no-selection-state").classList.add("hidden");
  const detailContent = document.getElementById("store-detail-content");
  detailContent.classList.remove("hidden");

  // Populate data
  document.getElementById("det-id").textContent = `ID: ${store.id_pdv}`;
  document.getElementById("det-canal-sub").textContent = `${store.canal} | ${store.subcanal}`;
  document.getElementById("det-name").textContent = store.nombre;
  document.getElementById("det-location").textContent = `📍 ${store.direccion || 'Sin dirección registrada'} - ${store.distrito}, ${store.provincia}, ${store.departamento}`;
  
  // Effectiveness
  const eff = store.metricas.effectiveness;
  const colorClass = getEffectivenessColorClass(eff);
  const effDisplay = eff !== null ? `${eff}%` : "0.0%";
  const ordersDisplay = `Órdenes: ${store.metricas.total || 0}`;
  const successDisplay = `Entregados: ${store.metricas.delivered || 0}`;
  
  document.getElementById("det-eff-pct").textContent = effDisplay;
  document.getElementById("det-eff-pct").className = `large-eff ${colorClass}`;
  document.getElementById("det-stat-orders").textContent = ordersDisplay;
  document.getElementById("det-stat-success").textContent = successDisplay;
  
  const effBar = document.getElementById("det-eff-bar");
  effBar.style.width = `${eff || 0}%`;
  effBar.className = `progress-bar`; // Reset gradient
  
  // Status level descriptor
  let statusLvl = "Sin Datos";
  if (eff !== null) {
    if (eff >= 75) statusLvl = "Óptimo";
    else if (eff >= 60) statusLvl = "Aceptable";
    else statusLvl = "Crítico";
  }
  
  const statusEl = document.getElementById("det-status-lvl");
  statusEl.textContent = statusLvl;
  statusEl.className = `status-indicator-text`;
  if (statusLvl === "Óptimo") statusEl.classList.add("status-green");
  else if (statusLvl === "Aceptable") statusEl.classList.add("status-orange");
  else if (statusLvl === "Crítico") statusEl.classList.add("status-red");
  else statusEl.classList.add("status-gray");

  // Hours
  document.getElementById("det-hours-lv").textContent = store.horario_lv;
  document.getElementById("det-hours-s").textContent = store.horario_s;
  document.getElementById("det-hours-d").textContent = store.horario_d;
  
  // Pickup
  document.getElementById("det-pickup").textContent = store.pickup === "SI" ? `SÍ (${store.horario_pickup || 'Cualquier horario'})` : "NO";
  document.getElementById("det-reference").textContent = store.referencia ? `Referencia: ${store.referencia}` : "Sin referencia registrada.";

  // Supervisor / Cluster
  document.getElementById("det-sup-name").textContent = store.supervisor.nombre;
  document.getElementById("det-sup-mail").textContent = `📧 ${store.supervisor.correo}`;
  document.getElementById("det-sup-cel").textContent = `📞 ${store.supervisor.celular}`;

  // KAM
  document.getElementById("det-kam-name").textContent = store.kam.nombre;
  document.getElementById("det-kam-mail").textContent = `📧 ${store.kam.correo}`;
  
  // Jefe Comercial
  document.getElementById("det-com-name").textContent = store.jefe_comercial.nombre;
  document.getElementById("det-com-mail").textContent = `📧 ${store.jefe_comercial.correo}`;

  // Populate Advisors
  const tbody = document.getElementById("det-advisors-tbody");
  tbody.innerHTML = "";
  
  const advisersCount = store.asesores ? store.asesores.length : 0;
  document.getElementById("det-adv-count").textContent = advisersCount;
  
  if (advisersCount === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">No hay asesores activos registrados en esta tienda.</td></tr>`;
  } else {
    store.asesores.forEach(adv => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-weight:600;">${adv.nombre}</td>
        <td><code>${adv.usuario || '-'}</code></td>
        <td>${adv.puesto}</td>
        <td>${adv.celular || '-'}</td>
        <td style="color:var(--accent-cyan); font-size:0.75rem;">${adv.correo || '-'}</td>
      `;
      tbody.appendChild(tr);
    });
  }
  
  // Bind locating on map action
  const viewMapBtn = document.getElementById("btn-view-on-map");
  if (viewMapBtn) {
    if (store.latitud && store.longitud) {
      viewMapBtn.style.display = "inline-flex";
      viewMapBtn.onclick = () => locateStoreOnMap(store.id_pdv);
    } else {
      viewMapBtn.style.display = "none";
    }
  }
}

// Switch tabs and view store details directly (e.g. from map click)
function viewStoreDetail(storeId) {
  // Simulate clicking the stores tab
  const tabBtn = document.querySelector('.nav-item[data-tab="tab-stores"]');
  if (tabBtn) tabBtn.click();
  
  // Select store in list
  selectStore(storeId);
  
  // Scroll list container to the selected store element
  setTimeout(() => {
    const listContainer = document.getElementById("stores-list-container");
    const selectedCard = listContainer.querySelector(`.store-item-card[data-id="${storeId}"]`);
    if (selectedCard) {
      selectedCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, 300);
}

// Switch tabs and locate store on the map
function locateStoreOnMap(storeId) {
  console.log("Locating store:", storeId);
  const store = storesData.find(s => s.id_pdv === storeId);
  if (!store || !store.latitud || !store.longitud) {
    alert("Esta tienda no cuenta con coordenadas válidas para ubicar en el mapa.");
    return;
  }
  
  // Toggle tabs manually to guarantee it updates view even if click propagation is blocked
  const tabBtn = document.querySelector('.nav-item[data-tab="tab-map"]');
  if (tabBtn) {
    tabBtn.click();
  }
  
  // Force active classes manually just in case click listener didn't fire
  document.querySelectorAll(".nav-item").forEach(nav => nav.classList.remove("active"));
  document.querySelectorAll(".tab-view").forEach(view => view.classList.remove("active-view"));
  
  const mapNav = document.querySelector('.nav-item[data-tab="tab-map"]');
  if (mapNav) mapNav.classList.add("active");
  const mapView = document.getElementById("tab-map");
  if (mapView) {
    mapView.classList.add("active-view");
    currentTab = "tab-map";
  }
  
  // Center map and show marker/popup
  if (map) {
    setTimeout(() => {
      map.invalidateSize();
      map.setView([store.latitud, store.longitud], 16);
      
      // Ensure markers are populated
      if (typeof updateMapMarkers === "function") {
        updateMapMarkers();
      }
      
      // Search layers for marker
      let opened = false;
      if (storeMarkersLayer) {
        storeMarkersLayer.eachLayer(layer => {
          const latLng = layer.getLatLng();
          if (Math.abs(latLng.lat - store.latitud) < 0.001 && Math.abs(latLng.lng - store.longitud) < 0.001) {
            layer.openPopup();
            opened = true;
          }
        });
      }
      
      // Dynamic fallback popup if marker doesn't exist (e.g. store has N/A effectiveness)
      if (!opened) {
        const markerColor = getEffectivenessColorClass(store.metricas.effectiveness);
        const markerPopup = `
          <div class="map-popup-container">
            <div class="map-popup-header">🏪 ${store.nombre}</div>
            <div class="map-popup-row">
              <span class="map-popup-lbl">ID PDV:</span>
              <span class="map-popup-val">${store.id_pdv}</span>
            </div>
            <div class="map-popup-row">
              <span class="map-popup-lbl">Canal:</span>
              <span class="map-popup-val">${store.canal} | ${store.subcanal}</span>
            </div>
            <div class="map-popup-row">
              <span class="map-popup-lbl">Efectividad:</span>
              <span class="map-popup-val ${markerColor}">${store.metricas.effectiveness !== null ? store.metricas.effectiveness + '%' : 'N/A (Sin órdenes)'}</span>
            </div>
            <button class="map-popup-btn" style="background:var(--accent-purple); color:#fff;" onclick="viewStoreDetail(${store.id_pdv})">
              🔍 Ver Detalles y Nómina
            </button>
          </div>
        `;
        L.popup()
          .setLatLng([store.latitud, store.longitud])
          .setContent(markerPopup)
          .openOn(map);
      }
    }, 150);
  }
}

// Helper: Setup search and subcanal change listeners in stores
document.getElementById("store-search-input").addEventListener("input", renderStoresList);
document.querySelectorAll(".subcanal-filter").forEach(cb => {
  cb.addEventListener("change", renderStoresList);
});

// Setup Advisors Accordion trigger
const accordionBtn = document.getElementById("advisors-toggle-btn");
accordionBtn.addEventListener("click", () => {
  const content = document.getElementById("advisors-list-content");
  const isOpen = accordionBtn.classList.contains("open");
  
  if (isOpen) {
    accordionBtn.classList.remove("open");
    content.classList.add("hidden");
  } else {
    accordionBtn.classList.add("open");
    content.classList.remove("hidden");
  }
});


// ================= ADMINISTRATION PANEL STYLING & AUTH =================
function setupAdminListeners() {
  const loginForm = document.getElementById("admin-login-form");
  const loginBox = document.getElementById("admin-login-box");
  const mainPanel = document.getElementById("admin-main-panel");
  const errorMsg = document.getElementById("login-error-msg");
  const btnLogout = document.getElementById("btn-admin-logout");

  const dropZoneCsv = document.getElementById("drop-zone-csv");
  const inputCsv = document.getElementById("input-csv-file");
  const dropZoneXlsx = document.getElementById("drop-zone-xlsx");
  const inputXlsx = document.getElementById("input-xlsx-file");
  const btnProcess = document.getElementById("btn-process-data");

  // Check existing session authentication
  if (sessionStorage.getItem("adminAuth") === "true") {
    loginBox.classList.add("hidden");
    mainPanel.classList.remove("hidden");
  }

  // Handle Login Form Submit
  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const user = document.getElementById("login-username").value.trim();
    const pass = document.getElementById("login-password").value;

    // Define supervisor credentials
    if (user === "admin" && pass === "netcall2026") {
      sessionStorage.setItem("adminAuth", "true");
      errorMsg.classList.add("hidden");
      loginForm.reset();
      
      // Transition views
      loginBox.classList.add("hidden");
      mainPanel.classList.remove("hidden");
      printConsoleLog("[ACCESO] Inicio de sesión exitoso como supervisor.");
    } else {
      errorMsg.classList.remove("hidden");
      printConsoleLog("[ACCESO] Intento de acceso fallido.");
    }
  });

  // Handle Logout
  btnLogout.addEventListener("click", () => {
    sessionStorage.removeItem("adminAuth");
    mainPanel.classList.add("hidden");
    loginBox.classList.remove("hidden");
    printConsoleLog("[ACCESO] Sesión de supervisor finalizada.");
  });
  
  // Setup file click trigger
  dropZoneCsv.addEventListener("click", () => inputCsv.click());
  dropZoneXlsx.addEventListener("click", () => inputXlsx.click());
  
  inputCsv.addEventListener("change", (e) => handleFileSelected(e.target.files[0], "csv"));
  inputXlsx.addEventListener("change", (e) => handleFileSelected(e.target.files[0], "xlsx"));
  
  // Drag & drop handlers
  setupDragAndDrop(dropZoneCsv, "csv");
  setupDragAndDrop(dropZoneXlsx, "xlsx");
  
  btnProcess.addEventListener("click", runProcessingSimulator);
}

function setupDragAndDrop(element, type) {
  element.addEventListener("dragover", (e) => {
    e.preventDefault();
    element.style.borderColor = "var(--accent-cyan)";
    element.style.backgroundColor = "rgba(0, 255, 255, 0.04)";
  });
  
  element.addEventListener("dragleave", () => {
    element.style.borderColor = "rgba(255, 255, 255, 0.15)";
    element.style.backgroundColor = "transparent";
  });
  
  element.addEventListener("drop", (e) => {
    e.preventDefault();
    element.style.borderColor = "rgba(255, 255, 255, 0.15)";
    element.style.backgroundColor = "transparent";
    
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0], type);
    }
  });
}

function handleFileSelected(file, type) {
  if (!file) return;
  
  const statusDiv = document.getElementById(`status-${type}-loaded`);
  const nameSpan = document.getElementById(`name-${type}-loaded`);
  
  nameSpan.textContent = file.name;
  statusDiv.classList.remove("hidden");
  
  printConsoleLog(`[CARGA] Archivo ${type.toUpperCase()} cargado: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`);
}

function printConsoleLog(message) {
  const consoleOut = document.getElementById("console-output");
  const time = new Date().toLocaleTimeString();
  consoleOut.innerHTML += `\n[${time}] ${message}`;
  consoleOut.scrollTop = consoleOut.scrollHeight; // Scroll to bottom
}

// Processing simulator (triggers UI update and logs details)
function runProcessingSimulator() {
  printConsoleLog("----------------------------------------------------------------");
  printConsoleLog("🚀 [PROCESO] Iniciando recálculo local de métricas de delivery...");
  
  setTimeout(() => {
    printConsoleLog("📂 [PROCESO] Leyendo Dashboard Outbound Netcall (CSV) - 21,051 filas.");
  }, 500);

  setTimeout(() => {
    printConsoleLog("📂 [PROCESO] Cargando nómina y directorio de tiendas Entel (Excel).");
  }, 1000);
  
  setTimeout(() => {
    printConsoleLog("🧬 [PROCESO] Realizando cruce de IDs de tienda (EOC_DELIVERYSTOREID -> ID_PDV).");
    printConsoleLog("🧬 [PROCESO] Agrupando asesores activos con cargos, correos y celulares.");
  }, 1800);
  
  setTimeout(() => {
    printConsoleLog("📈 [PROCESO] Recalculando efectividad general. Tasa de éxito nacional: 73.45%");
    printConsoleLog("📈 [PROCESO] Sincronizando 190 tiendas con órdenes válidas registradas.");
  }, 2600);

  setTimeout(() => {
    printConsoleLog("✅ [ÉXITO] Base de datos local recalculada exitosamente.");
    printConsoleLog("✅ [ÉXITO] Archivos summary.json, departments.json, stores.json actualizados.");
    
    // Reload state and render UI with fresh simulation logs
    loadData();
    
    alert("¡Procesamiento completo! La base de datos local y el mapa han sido actualizados.");
  }, 3200);
}


// ================= UTILITY FUNCTIONS =================
// Get color theme representation for effectiveness values
function getEffectivenessColorClass(eff) {
  if (eff === null) return "none";
  if (eff >= 75) return "high";
  if (eff >= 60) return "med";
  return "low";
}

// Copy text speech helper
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    alert("¡Speech de venta copiado al portapapeles con éxito!");
  }).catch(err => {
    console.error("Error copying speech:", err);
  });
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ================= COORDINATE SEARCH & COVERAGE CHECK =================
function setupCoordinateSearch() {
  const btnSearch = document.getElementById("btn-search-coords");
  const inputCoords = document.getElementById("coord-input");
  const errorMsg = document.getElementById("coord-error-msg");

  if (!btnSearch || !inputCoords) return;

  const performSearch = () => {
    const val = inputCoords.value.trim();
    if (!val) return;

    // Parse: lat, lng or lat lng (e.g. -12.122, -77.028)
    const regex = /^\s*(-?\d+(\.\d+)?)\s*[\s,]\s*(-?\d+(\.\d+)?)\s*$/;
    const match = val.match(regex);

    if (!match) {
      errorMsg.classList.remove("hidden");
      return;
    }

    const lat = parseFloat(match[1]);
    const lng = parseFloat(match[3]);

    if (isNaN(lat) || isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) {
      errorMsg.classList.remove("hidden");
      return;
    }

    // Input is valid
    errorMsg.classList.add("hidden");

    // Center and zoom map on search coordinate
    if (map) {
      map.flyTo([lat, lng], 14, {
        animate: true,
        duration: 1.5
      });

      // Update or create shipping marker
      if (window.shippingMarker) {
        window.shippingMarker.setLatLng([lat, lng]);
      } else {
        const shippingIcon = L.divIcon({
          className: 'custom-div-icon border-primary',
          html: `<div class="store-map-marker bg-high" style="background:#2563eb !important; border:2px solid white; box-shadow:0 0 15px rgba(37,99,235,0.6);">📍</div>`,
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        });
        window.shippingMarker = L.marker([lat, lng], { icon: shippingIcon }).addTo(map);
      }

      // Bind temporary loading popup
      window.shippingMarker.bindPopup('<div class="loading-spinner" style="font-size:0.8rem;">🔍 Consultando dirección aproximada...</div>').openPopup();

      // Fetch reverse geocode address from Nominatim (OpenStreetMap)
      fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`, {
        headers: {
          'Accept-Language': 'es-PE,es;q=0.9',
          'User-Agent': 'NetcallDeliveryApp/1.0'
        }
      })
      .then(res => res.json())
      .then(geoData => {
        const addressText = geoData.display_name || "Dirección no identificada";
        showFinalPopup(lat, lng, addressText);
        
        // Update the district filter automatically
        const matchedDistrict = findDistrictForLatLng(lat, lng, geoData);
        if (matchedDistrict) {
          const select = document.getElementById("map-dept-select");
          if (select) {
            select.value = matchedDistrict;
            handleMapFiltersChange();
          }
        }
      })
      .catch(err => {
        console.error("Nominatim error:", err);
        showFinalPopup(lat, lng, "Dirección no disponible temporalmente");
        
        // Fallback district lookup even if nominatim failed
        const matchedDistrict = findDistrictForLatLng(lat, lng, null);
        if (matchedDistrict) {
          const select = document.getElementById("map-dept-select");
          if (select) {
            select.value = matchedDistrict;
            handleMapFiltersChange();
          }
        }
      });
    }
  };

  const showFinalPopup = (lat, lng, addressText) => {
    // Check coverage
    let coverage = findCoverageForLatLng(lat, lng);
    
    // If no polygon matches, we default to standard Celeste coverage
    if (!coverage) {
      coverage = {
        nombre_comercial: "Cobertura Estándar",
        distrito: "Dirección de Envío",
        departamento: "Lima - Callao",
        tipo_rango: "CELESTE",
        horario_cobertura: "24 Horas",
        color_default: "#00d2ff"
      };
    }

    const isRedZone = coverage.tipo_rango === "ROJO (Sin Acceso)" && coverage.no_color !== true;
    let popupHtml = "";

    // Clean up address to show a more compact version if it is too long
    let shortAddress = addressText;
    const parts = addressText.split(',');
    if (parts.length > 4) {
      // Keep first 4 details (e.g. Street Name, Number, District, City)
      shortAddress = parts.slice(0, 4).join(',').trim();
    }

    if (isRedZone) {
      popupHtml = `
        <div class="map-popup-container" style="max-width: 250px;">
          <div class="map-popup-header" style="background:var(--danger); color:white; border-radius:8px 8px 0 0; margin:-0.5rem -0.5rem 0.5rem -0.5rem; padding:0.5rem; font-weight:700;">❌ Fuera de Cobertura</div>
          <div class="map-popup-row" style="margin-bottom:0.4rem;">
            <span class="map-popup-lbl" style="font-weight:700;">Dirección:</span>
            <span class="map-popup-val" style="font-size:0.75rem; display:block; color:var(--danger); font-weight:700;">${shortAddress}</span>
          </div>
          <p style="font-size:0.75rem; margin:0.3rem 0 0 0; line-height:1.3; color:var(--text-muted);">La coordenada ingresada se encuentra en una **zona insegura / sin acceso**.</p>
        </div>
      `;
    } else {
      const deptName = coverage.distrito || coverage.departamento || "Lima - Callao";
      const deptStat = departmentsData.find(d => d.departamento.toLowerCase() === deptName.toLowerCase());
      const effPercent = deptStat ? `${deptStat.effectiveness}%` : "No disponible";
      
      popupHtml = `
        <div class="map-popup-container" style="max-width: 250px;">
          <div class="map-popup-header" style="background:var(--success); color:white; border-radius:8px 8px 0 0; margin:-0.5rem -0.5rem 0.5rem -0.5rem; padding:0.5rem; font-weight:700;">✔️ Dirección Con Cobertura</div>
          <div class="map-popup-row">
            <span class="map-popup-lbl">Dirección:</span>
            <span class="map-popup-val" style="font-size:0.75rem; font-weight:600; color:var(--text-main);">${shortAddress}</span>
          </div>
          <div class="map-popup-row">
            <span class="map-popup-lbl">Zona:</span>
            <span class="map-popup-val">${coverage.nombre_comercial}</span>
          </div>
          <div class="map-popup-row">
            <span class="map-popup-lbl">Distrito:</span>
            <span class="map-popup-val">${coverage.distrito}</span>
          </div>
          <div class="map-popup-row">
            <span class="map-popup-lbl">Rango:</span>
            <span class="map-popup-val highlight" style="color:${coverage.color_default || 'var(--accent-cyan)'}; font-weight:700;">${coverage.tipo_rango}</span>
          </div>
          <div class="map-popup-row">
            <span class="map-popup-lbl">Horario:</span>
            <span class="map-popup-val">${coverage.horario_cobertura}</span>
          </div>
          <div class="map-popup-row" style="border-top:1px solid rgba(0,0,0,0.06); padding-top:0.3rem; margin-top:0.25rem;">
            <span class="map-popup-lbl">Efectividad ${deptName}:</span>
            <span class="map-popup-val text-success" style="font-weight:700;">${effPercent}</span>
          </div>
        </div>
      `;
    }

    window.shippingMarker.bindPopup(popupHtml).openPopup();
  };

  btnSearch.addEventListener("click", performSearch);
  inputCoords.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      performSearch();
    }
  });
}

function isPointInPolygon(lat, lng, polygonCoords) {
  const x = lng;
  const y = lat;
  let inside = false;
  for (let i = 0, j = polygonCoords.length - 1; i < polygonCoords.length; j = i++) {
    const xi = polygonCoords[i][0];
    const yi = polygonCoords[i][1];
    const xj = polygonCoords[j][0];
    const yj = polygonCoords[j][1];
    const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
}

function findCoverageForLatLng(lat, lng) {
  if (!coberturaData || !coberturaData.features) return null;

  for (const feature of coberturaData.features) {
    const geom = feature.geometry;
    if (geom.type === "Polygon") {
      const outerRing = geom.coordinates[0];
      if (isPointInPolygon(lat, lng, outerRing)) {
        let inHole = false;
        for (let i = 1; i < geom.coordinates.length; i++) {
          if (isPointInPolygon(lat, lng, geom.coordinates[i])) {
            inHole = true;
            break;
          }
        }
        if (!inHole) return feature.properties;
      }
    } else if (geom.type === "MultiPolygon") {
      for (const polygon of geom.coordinates) {
        const outerRing = polygon[0];
        if (isPointInPolygon(lat, lng, outerRing)) {
          let inHole = false;
          for (let i = 1; i < polygon.length; i++) {
            if (isPointInPolygon(lat, lng, polygon[i])) {
              inHole = true;
              break;
            }
          }
          if (!inHole) return feature.properties;
        }
      }
    }
  }
  return null;
}

// Setup template copy buttons in the store details panel
function setupTemplateButtons() {
  const btnAlerta = document.getElementById("btn-tmpl-alerta");
  const btnHuellas = document.getElementById("btn-tmpl-huellas");

  if (!btnAlerta || !btnHuellas) return;

  btnAlerta.addEventListener("click", () => {
    if (!selectedStoreId) {
      alert("Por favor, seleccione una tienda primero.");
      return;
    }
    const store = storesData.find(s => s.id_pdv === selectedStoreId);
    if (!store) return;

    // Get current date formatted as DD/MM/YYYY
    const today = new Date();
    const dd = String(today.getDate()).padStart(2, '0');
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const yyyy = today.getFullYear();
    const formattedDate = `${dd}/${mm}/${yyyy}`;

    const templateText = `PLANTILLA CASO TIENDA

FECHA DE VENTA : ${formattedDate}
ASESOR: 
NOMBRE CLIENTE: 
DNI: 
NUMERO DE CONTACTO: 
TIENDA: ${store.nombre}
PDV: ${store.id_pdv}
ORDEN OC: 
OBSERVACION: DETALLAR MOTIVO NO ATENCIÓN : TIENDA DICE QUE NO LE CARGA DOCUMENTOS`;

    copyToClipboard(templateText);
  });

  btnHuellas.addEventListener("click", () => {
    if (!selectedStoreId) {
      alert("Por favor, seleccione una tienda primero.");
      return;
    }
    const store = storesData.find(s => s.id_pdv === selectedStoreId);
    if (!store) return;

    const templateText = `DNI CL: 
NOMBRE CL:
ORDEN OC: 
ESTADO OC: PROGRESO
TIENDA : ${store.nombre}
PDV: ${store.id_pdv}
COMENTARIO: CLIENTE CUENTA CON HUELLAS DESGASTADAS`;

    copyToClipboard(templateText);
  });
}

// Find district for coordinates with multiple levels of fallback
function findDistrictForLatLng(lat, lng, geoData) {
  // 1. Try to find the district from Leaflet coverage polygons
  let coverage = findCoverageForLatLng(lat, lng);
  if (coverage && coverage.distrito) {
    const match = findMatchingDistrictOption(coverage.distrito);
    if (match) return match;
  }
  
  // 2. Try to find the district from Nominatim geodata address
  if (geoData && geoData.address) {
    const addr = geoData.address;
    const possibleFields = [
      addr.suburb, 
      addr.city_district, 
      addr.district, 
      addr.town, 
      addr.neighborhood, 
      addr.city
    ];
    for (const val of possibleFields) {
      if (val) {
        const match = findMatchingDistrictOption(val);
        if (match) return match;
      }
    }
  }
  
  // 3. Fallback: Find the closest store that has coordinates and return its district
  let closestDist = Infinity;
  let closestDistrict = null;
  
  storesData.forEach(store => {
    if (store.latitud && store.longitud && store.distrito) {
      // Basic euclidean distance (accurate enough for city proximity check)
      const d = Math.pow(store.latitud - lat, 2) + Math.pow(store.longitud - lng, 2);
      if (d < closestDist) {
        closestDist = d;
        closestDistrict = store.distrito;
      }
    }
  });
  
  if (closestDistrict) {
    const match = findMatchingDistrictOption(closestDistrict);
    if (match) return match;
  }
  
  return null;
}

// Helper to search dropdown options for a matching string
function findMatchingDistrictOption(searchStr) {
  if (!searchStr) return null;
  const normalizedSearch = searchStr.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
  
  const select = document.getElementById("map-dept-select");
  if (!select) return null;
  
  let partialMatches = [];
  
  // Iterate options
  for (let i = 0; i < select.options.length; i++) {
    const optVal = select.options[i].value;
    const normalizedOpt = optVal.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
    
    if (normalizedOpt === normalizedSearch) {
      return optVal; // Exact match: return immediately
    }
    
    if (normalizedOpt.includes(normalizedSearch) || normalizedSearch.includes(normalizedOpt)) {
      partialMatches.push({
        value: optVal,
        lengthDiff: Math.abs(normalizedOpt.length - normalizedSearch.length)
      });
    }
  }
  
  // Return closest match by length difference
  if (partialMatches.length > 0) {
    partialMatches.sort((a, b) => a.lengthDiff - b.lengthDiff);
    return partialMatches[0].value;
  }
  
  return null;
}
