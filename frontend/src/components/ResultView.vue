<script setup>
import { Icon } from '@iconify/vue'
import { ref, onMounted, watch, nextTick } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({ iconRetinaUrl, iconUrl, shadowUrl })

const props = defineProps({
  loading: Boolean,
  result: Object,
  error: { type: String, default: '' }
})

// ── Helpers ───────────────────────────────────────────────────────────────────

const parseAmenities = (amn) => Array.isArray(amn) ? amn : []

const isReadableAddress = (addr) => {
  if (!addr) return false
  return addr.replace(/[^a-zA-Z0-9\s,.\-]/g, '').trim().length > 5
}

const hasRealImage = (url) => url && url.startsWith('http')

const isValidCoord = (lat, lng) =>
  lat >= 9.0 && lat <= 15.5 && lng >= 102.0 && lng <= 108.0

const haversineDistance = (p1, p2) => {
  if (!p1.lat || !p1.lng || !p2.lat || !p2.lng) return null
  const R = 6371 // km
  const dLat = (p2.lat - p1.lat) * Math.PI / 180
  const dLng = (p2.lng - p1.lng) * Math.PI / 180
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(p1.lat * Math.PI / 180) * Math.cos(p2.lat * Math.PI / 180) *
            Math.sin(dLng / 2) * Math.sin(dLng / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

const formatDistance = (dist) => {
  if (dist === null) return null
  if (dist < 1) return `${Math.round(dist * 1000)}m`
  return `${dist.toFixed(1)}km`
}

const formatTime = (totalMinutes) => {
  const h = Math.floor(totalMinutes / 60) % 24
  const m = totalMinutes % 60
  const period = h >= 12 ? 'PM' : 'AM'
  const h12 = h % 12 || 12
  return `${h12}:${String(m).padStart(2, '0')} ${period}`
}

const formatTravelTime = (min) => {
  if (!min) return null
  if (min < 60) return `${min} min`
  const h = Math.floor(min / 60)
  const m = min % 60
  return m ? `${h}h ${m}m` : `${h}h`
}

// Build chronological schedule for one day
const getDaySchedule = (dayObj) => {
  const schedule = []
  let t = 8 * 60

  const stay = dayObj.stays?.[0]
  const activities = dayObj.activities || []
  const dining = dayObj.dining || []
  const actDuration = activities.length >= 4 ? 90 : 120
  const lunchAfterIdx = Math.max(0, Math.ceil(activities.length / 2) - 1)

  if (stay) {
    schedule.push({ place: stay, type: 'stay', timeLabel: formatTime(t), note: 'Depart Hotel' })
    t += 30
  }

  activities.forEach((act, i) => {
    schedule.push({ place: act, type: 'activity', timeLabel: formatTime(t), endTimeLabel: formatTime(t + actDuration) })
    t += actDuration + 30
    if (i === lunchAfterIdx && dining[0]) {
      t = Math.max(t, 12 * 60)
      schedule.push({ place: dining[0], type: 'dining', timeLabel: formatTime(t), endTimeLabel: formatTime(t + 90), note: 'Lunch' })
      t += 120
    }
  })

  const dinnerPlace = dining[1] ?? dining[0]
  if (dinnerPlace) {
    t = Math.max(t, 18 * 60)
    schedule.push({ place: dinnerPlace, type: 'dining', timeLabel: formatTime(t), endTimeLabel: formatTime(t + 90), note: 'Dinner' })
    t += 120
  }

  if (stay) {
    t = Math.max(t, 20 * 60)
    schedule.push({ place: stay, type: 'stay', timeLabel: formatTime(t), note: 'Return to Hotel' })
  }

  // Calculate distances between consecutive stops
  for (let i = 0; i < schedule.length - 1; i++) {
    const dist = haversineDistance(schedule[i].place, schedule[i + 1].place)
    schedule[i].distToNext = dist
  }

  return schedule
}

// Build ordered route from the full schedule (hotel → acts + meals → hotel)
const getDayRoute = (dayObj) => {
  return getDaySchedule(dayObj)
    .map(item => item.place)
    .filter(p => p.lat && p.lng && isValidCoord(p.lat, p.lng))
}

// ── Active day tab state ──────────────────────────────────────────────────────

const activeDay = ref(1)
const selectedPlace = ref(null)

const setDay = (day) => { 
  activeDay.value = day
  selectedPlace.value = null
}

// ── Map ───────────────────────────────────────────────────────────────────────

const mapContainer = ref(null)
const routeLoading = ref(false)
let mapInstance = null
let markersGroup = null
const markerMap = new Map()

// Fetch road geometry from OSRM (free, no API key).
// Falls back to straight lines if the request fails.
const fetchRoadRoute = async (places) => {
  if (places.length < 2) return places.map(p => [p.lat, p.lng])
  const coords = places.map(p => `${p.lng},${p.lat}`).join(';')
  try {
    const res = await fetch(
      `https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`,
      { signal: AbortSignal.timeout(8000) }
    )
    if (!res.ok) throw new Error('bad response')
    const data = await res.json()
    if (data.code === 'Ok' && data.routes?.[0]?.geometry?.coordinates?.length) {
      // OSRM returns [lng, lat]; Leaflet needs [lat, lng]
      return data.routes[0].geometry.coordinates.map(([lng, lat]) => [lat, lng])
    }
  } catch {
    console.warn('OSRM routing unavailable — drawing straight lines as fallback')
  }
  return places.map(p => [p.lat, p.lng])
}

const ROUTE_COLORS = ['#e74c3c', '#3498db', '#27ae60', '#f39c12', '#8e44ad', '#e67e22']

const SVG_BED  = `<path d="M7 13c1.66 0 3-1.34 3-3S8.66 7 7 7s-3 1.34-3 3 1.34 3 3 3zm12-6h-8v7H3V5H1v15h2v-3h18v3h2v-9c0-2.21-1.79-4-4-4z"/>`
const SVG_PIN  = `<path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>`
const SVG_FORK = `<path d="M11 9H9V2H7v7H5V2H3v7c0 2.12 1.66 3.84 3.75 3.97V22h2.5v-9.03C11.34 12.84 13 11.12 13 9V2h-2v7zm5-3v8h2.5v8H21V2c-2.76 0-5 2.24-5 4z"/>`

const makeMapIcon = (svgPath, bg, size = 34) => L.divIcon({
  html: `<div style="background:${bg};width:${size}px;height:${size}px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2.5px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.28)"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${Math.round(size*.54)}" height="${Math.round(size*.54)}" fill="white">${svgPath}</svg></div>`,
  iconSize: [size, size], iconAnchor: [size/2, size/2], popupAnchor: [0, -size/2], className: ''
})

const makeNumIcon = (num, bg, size = 30) => L.divIcon({
  html: `<div style="background:${bg};width:${size}px;height:${size}px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2.5px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.28);font-weight:800;font-size:13px;color:white;font-family:Inter,sans-serif">${num}</div>`,
  iconSize: [size, size], iconAnchor: [size/2, size/2], popupAnchor: [0, -size/2], className: ''
})

const makePopup = (place, t1, t2) => {
  const img = hasRealImage(place.image_url)
    ? `background-image:url('${place.image_url}');background-size:cover;background-position:center`
    : `background:#e2e8f0`
  const time = t1 ? `<div style="font-size:11px;color:#E5A517;font-weight:700;margin-top:5px">${t1}${t2 ? ' – ' + t2 : ''}</div>` : ''
  return `<div style="width:210px;font-family:Inter,sans-serif">
    <div style="height:110px;border-radius:8px 8px 0 0;${img}"></div>
    <div style="padding:10px 12px">
      <div style="font-size:10px;font-weight:800;color:#102050;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px">${place.category}</div>
      <div style="font-size:13px;font-weight:800;color:#0f172a;line-height:1.3">${place.title}</div>
      <div style="font-size:11px;color:#64748b;margin-top:3px">&#9733; ${place.rating} &middot; ${place.reviews} reviews</div>
      ${time}
    </div>
  </div>`
}

const initMap = () => {
  if (!mapContainer.value || mapInstance) return
  mapInstance = L.map(mapContainer.value).setView([12.5657, 104.9910], 7)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors', maxZoom: 18
  }).addTo(mapInstance)
  markersGroup = L.featureGroup().addTo(mapInstance)
}

const plotDay = async (dayNum) => {
  if (!mapInstance || !markersGroup || !props.result?.itinerary) return
  markersGroup.clearLayers()
  markerMap.clear()
  const dayObj = props.result.itinerary.find(d => d.day === dayNum)
  if (!dayObj) return

  const color = ROUTE_COLORS[(dayNum - 1) % ROUTE_COLORS.length]

  // Place all markers first so the map is interactive immediately
  let actNum = 0
  getDaySchedule(dayObj).forEach(item => {
    const p = item.place
    if (!p.lat || !p.lng || !isValidCoord(p.lat, p.lng)) return
    const icon = item.type === 'stay'
      ? makeMapIcon(SVG_BED, '#102050')
      : item.type === 'dining'
        ? makeMapIcon(SVG_FORK, '#c98e0e')
        : makeNumIcon(++actNum, color)
    const marker = L.marker([p.lat, p.lng], { icon })
      .bindPopup(makePopup(p, item.timeLabel, item.endTimeLabel), { 
        maxWidth: 230, 
        className: 'custom-popup',
        autoPan: false // Prevent popup from shifting the map away from center
      })
      .addTo(markersGroup)
    
    markerMap.set(p.title, marker)
  })

  if (markersGroup.getLayers().length > 0)
    try { mapInstance.fitBounds(markersGroup.getBounds(), { padding: [48, 48] }) } catch (_) {}

  // Fetch road-following route from OSRM (includes hotel + dining + activities)
  const routePlaces = getDayRoute(dayObj)
  if (routePlaces.length >= 2) {
    routeLoading.value = true
    const roadCoords = await fetchRoadRoute(routePlaces)
    routeLoading.value = false
    // Draw solid line if we got real road geometry, dashed as fallback
    const isRoad = roadCoords.length > routePlaces.length
    L.polyline(roadCoords, {
      color,
      weight: 4,
      opacity: 0.85,
      className: 'animated-path'
    }).addTo(markersGroup)
  }
}

const focusPlace = (place) => {
  if (!place.lat || !place.lng || !mapInstance) return
  selectedPlace.value = place.title
  
  // First open the popup
  const marker = markerMap.get(place.title)
  if (marker) marker.openPopup()
  
  // Use flyTo with a smoother curve to ensure it's dead center
  mapInstance.flyTo([place.lat, place.lng], 16, {
    animate: true,
    duration: 0.8,
    easeLinearity: 0.25
  })
}

watch(() => props.result, async (val) => {
  if (val?.itinerary) { await nextTick(); initMap(); await plotDay(activeDay.value) }
}, { deep: true })

watch(activeDay, (day) => { if (props.result?.itinerary) plotDay(day) })

onMounted(() => { if (props.result) { initMap(); plotDay(activeDay.value) } })
</script>

<template>
  <div class="rr">

    <!-- ── Loading ─────────────────────────────────────────────────── -->
    <div v-if="loading" class="state-view">
      <Icon icon="mdi:loading" class="spin" width="52" height="52" style="color:var(--accent-color)" />
      <h2>Crafting your itinerary…</h2>
      <p>Analysing thousands of locations for your perfect trip.</p>
    </div>

    <!-- ── Error ───────────────────────────────────────────────────── -->
    <div v-else-if="!result?.itinerary" class="state-view">
      <Icon icon="mdi:alert-circle-outline" width="48" height="48" style="color:var(--text-light);margin-bottom:.75rem" />
      <h2>Something went wrong</h2>
      <p>{{ error || "Couldn't generate a trip. Try adjusting your filters." }}</p>
      <button class="btn-primary" @click="$emit('restart')">Try Again</button>
    </div>

    <!-- ── Main result layout ──────────────────────────────────────── -->
    <div v-else class="trip-layout">

      <!-- Top bar: title + start over -->
      <header class="trip-bar">
        <div class="trip-bar-left">
          <span class="chip">
            <Icon icon="mdi:check-circle-outline" width="12" height="12" />
            Trip Ready
          </span>
          <h1 class="trip-title">{{ result.total_days }} Days in <em>{{ result.province }}</em></h1>
        </div>
        <button class="btn-outline" @click="$emit('restart')">
          <Icon icon="mdi:refresh" width="15" height="15" />
          Start Over
        </button>
      </header>

      <!-- Day tab bar -->
      <nav class="day-tabs-container">
        <div class="day-tabs">
          <div 
            class="day-pill-bg" 
            :style="{ 
              width: `calc(100% / ${result.itinerary.length})`,
              transform: `translateX(${(activeDay - 1) * 100}%)`
            }"
          ></div>
          <button
            v-for="dayObj in result.itinerary"
            :key="dayObj.day"
            class="day-tab"
            :class="{ active: activeDay === dayObj.day }"
            @click="setDay(dayObj.day)"
          >
            <span class="dt-label">Day {{ dayObj.day }}</span>
            <span class="dt-meta" v-if="dayObj.distance_km > 0">
              {{ dayObj.distance_km }} km
            </span>
          </button>
        </div>
      </nav>

      <!-- Body: schedule list + map -->
      <div class="trip-body">

        <!-- Schedule pane (scrolls naturally) -->
        <div class="schedule-pane">
          <template v-for="dayObj in result.itinerary" :key="dayObj.day">
            <TransitionGroup 
              v-show="activeDay === dayObj.day" 
              name="stagger" 
              tag="div" 
              class="schedule"
            >
              <div
                v-for="(item, idx) in getDaySchedule(dayObj)"
                :key="item.place.title + idx"
                class="sched-row"
                :class="['t-' + item.type, { 'selected': selectedPlace === item.place.title }]"
                :style="{ '--index': idx }"
              >
                <!-- Time -->
                <div class="sched-time">
                  <span class="st-start">{{ item.timeLabel }}</span>
                  <span v-if="item.endTimeLabel" class="st-end">{{ item.endTimeLabel }}</span>
                </div>

                <!-- Track -->
                <div class="sched-track">
                  <div class="track-line" v-if="idx > 0"></div>
                  <div class="track-dot">
                    <Icon
                      :icon="item.type === 'stay' ? 'mdi:bed-outline' : item.type === 'dining' ? 'mdi:silverware-fork-knife' : 'mdi:map-marker-outline'"
                      width="12" height="12"
                    />
                  </div>
                  <div class="track-line" v-if="idx < getDaySchedule(dayObj).length - 1"></div>
                  
                  <div v-if="item.distToNext && item.distToNext > 0.05" class="dist-bubble">
                    {{ formatDistance(item.distToNext) }}
                  </div>
                </div>

                <!-- Card -->
                <div class="sched-card">
                  <p class="scard-note" v-if="item.note">{{ item.note }}</p>
                  <div 
                    class="place-card" 
                    :class="{ 'selected': selectedPlace === item.place.title }"
                    @click="focusPlace(item.place)"
                  >
                    <!-- Image -->
                    <div
                      class="pc-img"
                      :style="hasRealImage(item.place.image_url) ? { backgroundImage: `url(${item.place.image_url})` } : {}"
                    >
                      <div v-if="!hasRealImage(item.place.image_url)" class="pc-img-empty">
                        <Icon icon="mdi:image-off-outline" width="26" height="26" style="color:#b0bec5" />
                      </div>
                      <span class="pc-rating" v-if="item.place.rating !== 'No Rating'">
                        <Icon icon="mdi:star" width="10" height="10" style="color:#E5A517" />
                        {{ item.place.rating }}
                      </span>
                    </div>
                    <!-- Info -->
                    <div class="pc-info">
                      <span class="pc-cat">{{ item.place.category }}</span>
                      <span class="pc-name">{{ item.place.title }}</span>
                      <span class="pc-addr" v-if="isReadableAddress(item.place.address)">
                        <Icon icon="mdi:map-marker-outline" width="10" height="10" />
                        {{ item.place.address }}
                      </span>
                      <p class="pc-desc">{{ item.place.description }}</p>
                      <div class="pc-tags">
                        <span v-for="a in parseAmenities(item.place.amenities).slice(0,5)" :key="a" class="pc-tag">{{ a }}</span>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </TransitionGroup>
          </template>
        </div>

        <!-- Map pane (sticky) -->
        <div class="map-pane">
          <!-- Info overlay -->
          <div class="map-card" v-if="result.itinerary">
            <div class="mc-row">
              <span class="mc-day">Day {{ activeDay }}</span>
              <span class="mc-stats" v-if="result.itinerary[activeDay-1]?.distance_km > 0">
                <Icon icon="mdi:map-marker-distance" width="12" height="12" />
                {{ result.itinerary[activeDay-1].distance_km }} km
                <span v-if="result.itinerary[activeDay-1].travel_time_min > 0">
                  &nbsp;&middot;&nbsp;
                  <Icon icon="mdi:clock-outline" width="12" height="12" />
                  {{ formatTravelTime(result.itinerary[activeDay-1].travel_time_min) }} drive
                </span>
              </span>
            </div>
            <div class="mc-legend">
              <span class="leg"><span class="leg-dot" style="background:#102050"></span>Hotel</span>
              <span class="leg"><span class="leg-dot" style="background:#e74c3c"></span>Activity</span>
              <span class="leg"><span class="leg-dot" style="background:#c98e0e"></span>Dining</span>
            </div>
            <div v-if="routeLoading" class="mc-routing">
              <Icon icon="mdi:loading" class="spin-sm" width="12" height="12" />
              Loading route…
            </div>
          </div>
          <div ref="mapContainer" class="map-el"></div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Root ─────────────────────────────────────────────────────────────────── */
.rr {
  width: 100%;
  height: 100%;        /* fill .result-page */
  min-height: 0;
  background: var(--surface-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── State views (loading / error) ───────────────────────────────────────── */
.state-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 3rem 2rem;
  gap: 0.5rem;
}

.state-view h2 { font-size: 1.4rem; font-weight: 800; color: var(--primary-color); }
.state-view p  { color: var(--text-secondary); font-size: 0.9rem; max-width: 320px; }

@keyframes spin { to { transform: rotate(360deg) } }
.spin { animation: spin 1.1s linear infinite; margin-bottom: 0.75rem; }

/* ── Trip layout ─────────────────────────────────────────────────────────── */
.trip-layout {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;        /* CRITICAL: flex child must shrink */
  overflow: hidden;
}

/* ── Top bar ─────────────────────────────────────────────────────────────── */
.trip-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.1rem 1.75rem 0.9rem;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.trip-bar-left { display: flex; flex-direction: column; gap: 0.2rem; }

.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: rgba(229,165,23,.1);
  color: var(--accent-color);
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.18rem 0.55rem;
  border-radius: 9999px;
  width: fit-content;
}

.trip-title {
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--primary-color);
  line-height: 1.2;
}

.trip-title em { font-style: normal; color: var(--accent-color); }

/* ── Day tab bar ─────────────────────────────────────────────────────────── */
.day-tabs-container {
  padding: 0.75rem 1.75rem;
  border-bottom: 1px solid var(--border-color);
  background: var(--surface-color);
  display: flex;
  justify-content: flex-start;
}

.day-tabs {
  position: relative;
  display: flex;
  background: var(--bg-color);
  padding: 4px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.day-pill-bg {
  position: absolute;
  top: 4px;
  left: 4px;
  height: calc(100% - 8px);
  background: white;
  border-radius: 9px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  z-index: 1;
}

.day-tab {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1.5rem;
  min-width: 100px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: color 0.3s ease;
  border-radius: 9px;
}

.day-tab:hover .dt-label {
  color: var(--primary-color);
}

.day-tab.active .dt-label {
  color: var(--primary-color);
}

.dt-label {
  font-size: 0.85rem;
  font-weight: 800;
  color: var(--text-secondary);
}

.dt-meta {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--text-light);
}

/* ── Trip body: the two-panel area ───────────────────────────────────────── */
.trip-body {
  display: flex;
  flex: 1;
  min-height: 0;   /* CRITICAL — without this, flex children ignore overflow */
  overflow: hidden;
}

/* ── Schedule pane (left) — scrolls within itself ────────────────────────── */
.schedule-pane {
  flex: 0 0 46%;
  min-height: 0;
  overflow-y: auto;      /* only this panel scrolls */
  overflow-x: hidden;
  padding: 1.5rem 1.5rem 3rem;
  background: var(--bg-color);
  border-right: 1px solid var(--border-color);
}

.schedule-pane::-webkit-scrollbar { width: 5px; }
.schedule-pane::-webkit-scrollbar-track { background: transparent; }
.schedule-pane::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 10px; }

.schedule { display: flex; flex-direction: column; }

/* ── Schedule row ────────────────────────────────────────────────────────── */
.sched-row {
  display: grid;
  grid-template-columns: 64px 24px 1fr;
  column-gap: 16px;
  align-items: stretch;
  position: relative;
}

/* Stagger Animation */
.stagger-enter-active {
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  transition-delay: calc(var(--index) * 0.08s);
}
.stagger-enter-from {
  opacity: 0;
  transform: translateY(24px) scale(0.98);
}

/* Time column */
.sched-time {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding-top: 12px;
  gap: 0;
}

.st-start {
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--primary-color);
  white-space: nowrap;
  line-height: 1.2;
}

.st-end {
  font-size: 0.58rem;
  font-weight: 500;
  color: var(--text-light);
  white-space: nowrap;
  line-height: 1.2;
}

/* Track column */
.sched-track {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.track-line {
  flex: 1;
  width: 4px;
  min-height: 20px;
  background: var(--border-color);
  opacity: 0.5;
  border-radius: 2px;
}

.dist-bubble {
  position: absolute;
  bottom: -11px; /* Center it exactly in the gap between dots */
  left: 50%;
  transform: translateX(-50%);
  background: white;
  border: 1.5px solid var(--border-color);
  border-radius: 999px;
  padding: 0.1rem 0.45rem;
  font-size: 0.62rem;
  font-weight: 800;
  color: var(--text-light);
  white-space: nowrap;
  z-index: 10;
  box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}

/* ... (track-dot same) */

.track-dot {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 3px solid white;
  box-shadow: 0 4px 10px rgba(0,0,0,0.15);
  color: white;
  z-index: 1;
  transition: all 0.3s ease;
}

.t-stay .track-dot     { background: var(--primary-color); }
.t-activity .track-dot { background: var(--accent-color); color: var(--primary-color); }
.t-dining .track-dot   { background: #c98e0e; }

.sched-row.selected .track-dot {
  transform: scale(1.2);
  box-shadow: 0 0 15px var(--accent-color);
  border-color: var(--accent-color);
}

/* Card column */
.sched-card { padding: 8px 0 20px; }

.scard-note {
  font-size: 0.65rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--text-light);
  margin: 0 0 8px 4px;
}

/* ── Place card ──────────────────────────────────────────────────────────── */
.place-card {
  display: flex;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.04);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
}

.place-card:hover {
  box-shadow: 0 10px 30px rgba(0,0,0,0.06);
  transform: translateY(-2px);
  border-color: rgba(0, 0, 0, 0.08);
}

.place-card.selected {
  border-color: var(--accent-color);
  box-shadow: 0 10px 30px rgba(229, 165, 23, 0.12);
  background: rgba(229, 165, 23, 0.02);
  transform: scale(1.01);
}

.pc-img {
  width: 130px;
  flex-shrink: 0;
  background-size: cover;
  background-position: center;
  background-color: #f1f5f9;
  position: relative;
  border-right: 1px solid rgba(0, 0, 0, 0.04);
  min-height: 120px;
}

.pc-img-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #102050 0%, #1e293b 100%);
  opacity: 0.9;
}

.pc-img-empty .iconify {
  color: var(--accent-color) !important;
  opacity: 0.5;
}

.pc-rating {
  position: absolute;
  top: 8px;
  right: 8px;
  bottom: auto;
  left: auto;
  background: white;
  font-size: 0.7rem;
  font-weight: 800;
  color: var(--primary-color);
  padding: 0.2rem 0.5rem;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.pc-info {
  padding: 1rem 1.25rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 0;
}

.pc-cat {
  font-size: 0.62rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--accent-hover);
}

.pc-name {
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--primary-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
}

.pc-addr {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  color: var(--text-light);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.pc-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.pc-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.pc-tag {
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--primary-color);
  background: rgba(16, 32, 80, 0.04);
  border-radius: 6px;
  padding: 0.2rem 0.6rem;
}

/* ── Map pane (right) — fills remaining space, never scrolls ─────────────── */
.map-pane {
  flex: 1;
  min-height: 0;
  position: relative;
  background: #e8ecf0;
  overflow: hidden;
}

.map-el { position: absolute; inset: 0; }

/* Map info card */
.map-card {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 1000;
  background: rgba(255,255,255,.96);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 0.65rem 0.9rem;
  box-shadow: 0 4px 20px rgba(0,0,0,.1);
  min-width: 156px;
}

.mc-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.45rem;
}

.mc-day {
  font-size: 0.85rem;
  font-weight: 800;
  color: var(--primary-color);
}

.mc-stats {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.73rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.mc-legend {
  display: flex;
  gap: 0.65rem;
  border-top: 1px solid var(--border-color);
  padding-top: 0.4rem;
}

.leg {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.68rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.leg-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

.mc-routing {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.68rem;
  color: var(--text-secondary);
  border-top: 1px solid var(--border-color);
  padding-top: 0.4rem;
  margin-top: 0.3rem;
}

@keyframes spin-sm { to { transform: rotate(360deg) } }
.spin-sm { animation: spin-sm 1s linear infinite; }

/* ── Map Animated Path ───────────────────────────────────────────────────── */
:deep(.animated-path) {
  stroke-dasharray: 10, 10;
  animation: dash-move 1.5s linear infinite;
}

@keyframes dash-move {
  to {
    stroke-dashoffset: -20;
  }
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.btn-primary {
  background: var(--accent-color);
  color: var(--primary-color);
  padding: 0.55rem 1.25rem;
  font-size: 0.9rem;
  font-weight: 700;
  border-radius: var(--radius-md);
  margin-top: 0.75rem;
  border: none;
  cursor: pointer;
  transition: background .2s;
}
.btn-primary:hover { background: var(--accent-hover); }

.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  white-space: nowrap;
  background: transparent;
  color: var(--text-secondary);
  border: 1.5px solid var(--border-color);
  padding: 0.45rem 0.9rem;
  font-weight: 700;
  font-size: 0.82rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all .15s;
  flex-shrink: 0;
}
.btn-outline:hover { background: var(--bg-color); border-color: var(--text-secondary); color: var(--text-primary); }

:deep(.leaflet-popup-content-wrapper) {
  padding: 0; border-radius: 10px; overflow: hidden; box-shadow: 0 8px 24px rgba(0,0,0,.14);
}
:deep(.leaflet-popup-content) { margin: 0; line-height: 1.4; }
:deep(.leaflet-popup-tip-container) { padding: 0; }

/* ── Responsive ───────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .trip-body { flex-direction: column; }
  .schedule-pane {
    flex: 0 0 55%;   /* takes 55% of the column height on tablet */
    overflow-y: auto;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    padding: 1.25rem;
  }
  .map-pane { flex: 1; min-height: 260px; }
}

@media (max-width: 600px) {
  .trip-bar { padding: 0.9rem 1rem; }
  .day-tabs { padding: 0 1rem; }
  .pc-img { width: 90px; }
  .sched-row { grid-template-columns: 62px 22px 1fr; }
  .trip-title { font-size: 1.2rem; }
}
</style>
