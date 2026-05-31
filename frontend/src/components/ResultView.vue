<script setup>
import { Icon } from '@iconify/vue'
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
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

const emit = defineEmits(['restart', 'go-home'])

// ── Helpers ───────────────────────────────────────────────────────────────────

const parseAmenities = (amn) => Array.isArray(amn) ? amn : []

const isReadableAddress = (addr) => {
  if (!addr) return false
  return addr.replace(/[^a-zA-Z0-9\s,.\-]/g, '').trim().length > 5
}

const hasRealImage = (url) => url && (url.startsWith('http') || url.startsWith('/'))

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

  for (let i = 0; i < schedule.length - 1; i++) {
    const dist = haversineDistance(schedule[i].place, schedule[i + 1].place)
    schedule[i].distToNext = dist
  }

  return schedule
}

const getDayRoute = (dayObj) => {
  return getDaySchedule(dayObj)
    .map(item => item.place)
    .filter(p => p.lat && p.lng && isValidCoord(p.lat, p.lng))
}

// ── Display state ─────────────────────────────────────────────────────────────

const showFullLoading = computed(() => props.loading && !props.result?.itinerary)
const showError       = computed(() => !props.loading && !props.result?.itinerary)
const showDashboard   = computed(() => !!props.result?.itinerary)
const isRerolling     = computed(() => props.loading && !!props.result?.itinerary)

// ── State ───────────────────────────────────────────────────────────────────

const activeDay = ref(1)
const selectedPlace = ref(null)
const isMapFull = ref(false)

const setDay = (day) => { 
  activeDay.value = day
  selectedPlace.value = null
}

const toggleMap = () => {
  isMapFull.value = !isMapFull.value
  setTimeout(() => mapInstance?.invalidateSize(), 300)
}

// ── Map ───────────────────────────────────────────────────────────────────────

const mapContainer = ref(null)
const timelineContainer = ref(null)
const routeLoading = ref(false)

const handleTimelineScroll = (e) => {
  const scrollEvent = new CustomEvent('internal-scroll', {
    detail: { scrollTop: e.target.scrollTop }
  })
  window.dispatchEvent(scrollEvent)
}

const loadingMessages = [
  "Consulting local experts...",
  "Finding hidden gems...",
  "Optimizing your travel route...",
  "Selecting authentic Khmer dining...",
  "Balancing your adventure...",
  "Finalizing your personalized plan..."
]
const currentMessageIndex = ref(0)
let messageInterval = null

watch(() => props.loading, (isLoading) => {
  if (isLoading) {
    currentMessageIndex.value = 0
    messageInterval = setInterval(() => {
      currentMessageIndex.value = (currentMessageIndex.value + 1) % loadingMessages.length
    }, 2500)
  } else {
    clearInterval(messageInterval)
  }
}, { immediate: true })

let mapInstance = null
let markersGroup = null
const markerMap = new Map()

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
      return data.routes[0].geometry.coordinates.map(([lng, lat]) => [lat, lng])
    }
  } catch {
    console.warn('OSRM routing unavailable')
  }
  return places.map(p => [p.lat, p.lng])
}

const ROUTE_COLORS = ['#102050', '#E5A517', '#1ABC9C', '#8E44AD', '#E74C3C', '#2C3E50']

const SVG_BED  = `<path d="M7 13c1.66 0 3-1.34 3-3S8.66 7 7 7s-3 1.34-3 3 1.34 3 3 3zm12-6h-8v7H3V5H1v15h2v-3h18v3h2v-9c0-2.21-1.79-4-4-4z"/>`
const SVG_PIN  = `<path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>`
const SVG_FORK = `<path d="M11 9H9V2H7v7H5V2H3v7c0 2.12 1.66 3.84 3.75 3.97V22h2.5v-9.03C11.34 12.84 13 11.12 13 9V2h-2v7zm5-3v8h2.5v8H21V2c-2.76 0-5 2.24-5 4z"/>`

const makeMapIcon = (svgPath, bg, size = 32) => L.divIcon({
  html: `<div style="background:${bg};width:${size}px;height:${size}px;border-radius:2px;display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:var(--shadow-md)"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="white">${svgPath}</svg></div>`,
  iconSize: [size, size], iconAnchor: [size/2, size/2], popupAnchor: [0, -size/2], className: ''
})

const makeNumIcon = (num, bg, size = 28) => L.divIcon({
  html: `<div style="background:${bg};width:${size}px;height:${size}px;border-radius:2px;display:flex;align-items:center;justify-content:center;border:2px solid #fff;box-shadow:var(--shadow-md);font-weight:800;font-size:12px;color:white;font-family:Inter,sans-serif">${num}</div>`,
  iconSize: [size, size], iconAnchor: [size/2, size/2], popupAnchor: [0, -size/2], className: ''
})

const initMap = () => {
  if (!mapContainer.value || mapInstance) return
  mapInstance = L.map(mapContainer.value, { zoomControl: false }).setView([12.5657, 104.9910], 7)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(mapInstance)
  L.control.zoom({ position: 'bottomright' }).addTo(mapInstance)
  markersGroup = L.featureGroup().addTo(mapInstance)
}

const plotDay = async (dayNum) => {
  if (!mapInstance || !markersGroup || !props.result?.itinerary) return
  markersGroup.clearLayers()
  markerMap.clear()
  const dayObj = props.result.itinerary.find(d => d.day === dayNum)
  if (!dayObj) return

  const color = ROUTE_COLORS[(dayNum - 1) % ROUTE_COLORS.length]

  let actNum = 0
  getDaySchedule(dayObj).forEach(item => {
    const p = item.place
    if (!p.lat || !p.lng || !isValidCoord(p.lat, p.lng)) return
    const icon = item.type === 'stay'
      ? makeMapIcon(SVG_BED, 'hsl(var(--primary))')
      : item.type === 'dining'
        ? makeMapIcon(SVG_FORK, 'hsl(var(--gold))')
        : makeNumIcon(++actNum, color)
    const marker = L.marker([p.lat, p.lng], { icon }).addTo(markersGroup)

    // Add interactive popup
    const popupContent = `
      <div style="font-family: 'Inter', sans-serif; min-width: 180px; padding: 2px;">
        ${hasRealImage(p.image_url) ? `
          <div style="width: 100%; height: 100px; background-image: url('${p.image_url}'); background-size: cover; background-position: center; border-radius: 4px; margin-bottom: 8px; background-color: #102050;"></div>
        ` : ''}
        <div style="padding: 0 2px;">
          <div style="font-weight: 800; color: #102050; font-size: 14px; line-height: 1.2; margin-bottom: 2px;">${p.title}</div>
          <div style="font-size: 10px; color: #E5A517; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">${p.category}</div>
          ${isReadableAddress(p.address) ? `<div style="font-size: 11px; color: #64748b; margin-top: 6px; line-height: 1.3;">${p.address}</div>` : ''}
        </div>
      </div>
    `
    marker.bindPopup(popupContent, { 
      closeButton: false, 
      offset: L.point(0, -15),
      className: 'custom-map-popup'
    })

    // Click marker to focus in timeline
    marker.on('click', () => {
      selectedPlace.value = p.title
    })

    markerMap.set(p.title, marker)
  })

  if (markersGroup.getLayers().length > 0)
    try { mapInstance.fitBounds(markersGroup.getBounds(), { padding: [60, 60] }) } catch (_) {}

  const routePlaces = getDayRoute(dayObj)
  if (routePlaces.length >= 2) {
    routeLoading.value = true
    const roadCoords = await fetchRoadRoute(routePlaces)
    routeLoading.value = false
    // Background track — wide, faded, gives the "road" feel
    L.polyline(roadCoords, {
      color,
      weight: 8,
      opacity: 0.12,
    }).addTo(markersGroup)

    // Animated direction trail — flowing dashes show travel direction
    L.polyline(roadCoords, {
      color,
      weight: 3,
      opacity: 0.9,
      dashArray: '10 7',
      className: 'route-trail'
    }).addTo(markersGroup)
  }
}

const focusPlace = (place) => {
  if (!place.lat || !place.lng || !mapInstance) return
  selectedPlace.value = place.title
  mapInstance.flyTo([place.lat, place.lng], 15, { duration: 0.8 })
  
  // Open marker popup
  const marker = markerMap.get(place.title)
  if (marker) {
    marker.openPopup()
  }
}

watch(() => props.result, async (val) => {
  if (val?.itinerary) {
    activeDay.value = 1
    selectedPlace.value = null
    await nextTick()
    initMap()
    await plotDay(1)
  }
}, { deep: true })

watch(activeDay, (day) => { if (props.result?.itinerary) plotDay(day) })

onMounted(() => { 
  if (props.result) { initMap(); plotDay(activeDay.value) } 
  if (timelineContainer.value) {
    timelineContainer.value.addEventListener('scroll', handleTimelineScroll, { passive: true })
  }
})

onBeforeUnmount(() => {
  if (messageInterval) clearInterval(messageInterval)
  if (timelineContainer.value) {
    timelineContainer.value.removeEventListener('scroll', handleTimelineScroll)
  }
})
</script>

<template>
  <div class="result-container" :class="{ 'map-expanded': isMapFull }">

    <!-- ── State views ───────────────────────────────────────── -->
    <div v-if="showFullLoading" class="overlay-view loading-overlay">
      

      <div class="loading-content">
        <div class="lottie-container">
          <dotlottie-wc 
            src="https://lottie.host/7f58f712-2682-44e4-ace4-fe2a09a5642d/Sx57y2ZMT5.lottie" 
            style="width: 320px; height: 320px" 
            :autoplay="true" 
            :loop="true"
          ></dotlottie-wc>
        </div>
        
        <div class="loading-text-wrapper">
          <h2 class="loading-title">Creating Your Journey</h2>
          <Transition name="fade-up" mode="out-in">
            <p :key="currentMessageIndex" class="loading-subtitle">
              {{ loadingMessages[currentMessageIndex] }}
            </p>
          </Transition>
        </div>

        <div class="loading-progress-bar">
          <div class="progress-fill"></div>
        </div>
      </div>
    </div>

    <div v-else-if="showError" class="overlay-view">
      <div class="error-box nextgen-card">
        <Icon icon="mdi:alert-circle-outline" width="48" height="48" style="color:#ef4444" />
        <h2>Generation Failed</h2>
        <p>{{ error || "We couldn't create a valid itinerary with these preferences." }}</p>
        <div style="display:flex;gap:0.75rem;flex-wrap:wrap;justify-content:center">
          <button class="btn-primary" @click="$emit('restart')">Try Again</button>
          <button class="btn-secondary" @click="$emit('go-home')">Edit Search</button>
        </div>
      </div>
    </div>

    <!-- ── Dashboard Layout ──────────────────────────────────────── -->
    <div v-else-if="showDashboard" class="dashboard">
      
      <!-- Side Navigation / Itinerary Pane -->
      <aside class="itinerary-pane">
        
        <!-- Compact Header -->
        <header class="pane-header">
          <div class="header-main">
            <div class="title-group">
              <h1 class="itinerary-title">Trip to {{ result.province }}</h1>
              <div class="header-meta">
                <span class="meta-item">{{ result.total_days }} Days</span>
                <span class="meta-dot"></span>
                <span class="meta-item">{{ result.itinerary.reduce((acc, d) => acc + (d.activities?.length || 0), 0) }} Sites</span>
                <template v-if="result.itinerary[activeDay - 1]">
                  <span class="meta-dot"></span>
                  <span class="meta-item text-gold">{{ result.itinerary[activeDay - 1].distance_km }} KM Today</span>
                </template>
              </div>
            </div>
            <div class="header-actions">
              <button class="btn-action" @click="$emit('restart')" title="New suggestions (same route)" :disabled="isRerolling">
                <Icon icon="lucide:shuffle" width="14" height="14" :class="{ 'spin-icon': isRerolling }" />
              </button>
              <button class="btn-action" @click="$emit('go-home')" title="Edit search">
                <Icon icon="lucide:sliders-horizontal" width="14" height="14" />
              </button>
            </div>
          </div>
        </header>

        <!-- Day Selector -->
        <nav class="day-nav">
          <div class="day-scroll">
            <button 
              v-for="d in result.itinerary" 
              :key="d.day"
              class="day-chip"
              :class="{ active: activeDay === d.day }"
              @click="setDay(d.day)"
            >
              Day {{ d.day }}
            </button>
          </div>
        </nav>

        <!-- Timeline Content -->
        <main ref="timelineContainer" class="timeline-container">

          <!-- Skeleton while rerolling -->
          <div v-if="isRerolling" class="skeleton-timeline">
            <div v-for="i in 5" :key="i" class="skeleton-row">
              <div class="skel-marker-col">
                <div class="skel skel-time"></div>
                <div class="skel skel-dot"></div>
                <div class="skel skel-line"></div>
              </div>
              <div class="skel-card">
                <div class="skel skel-img"></div>
                <div class="skel-info">
                  <div class="skel skel-tag"></div>
                  <div class="skel skel-title"></div>
                  <div class="skel skel-addr"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Real content -->
          <template v-else v-for="dayObj in result.itinerary" :key="dayObj.day">
            <div v-if="activeDay === dayObj.day" class="timeline">
              <div
                v-for="(item, idx) in getDaySchedule(dayObj)"
                :key="item.place.title + idx"
                class="timeline-item"
                :class="['type-' + item.type, { 'is-selected': selectedPlace === item.place.title }]"
                @click="focusPlace(item.place)"
              >
                <!-- Time/Marker Column -->
                <div class="item-marker">
                  <span class="item-time">{{ item.timeLabel }}</span>
                  <div class="marker-dot">
                    <Icon :icon="item.type === 'stay' ? 'lucide:hotel' : item.type === 'dining' ? 'lucide:utensils' : 'lucide:map-pin'" width="14" height="16" />
                  </div>
                  <div class="marker-line" v-if="idx < getDaySchedule(dayObj).length - 1"></div>
                </div>

                <!-- Card Column -->
                <div class="item-content">
                  <div class="place-preview nextgen-card">
                    <div
                      class="preview-img"
                      :style="hasRealImage(item.place.image_url) ? { backgroundImage: `url(${item.place.image_url})` } : {}"
                    >
                      <div class="rating-badge" v-if="item.place.rating && item.place.rating !== 'No Rating'">
                        <Icon icon="mdi:star" width="10" height="10" />
                        {{ item.place.rating }}
                      </div>
                    </div>
                    <div class="preview-info">
                      <div class="info-tags">
                        <span class="item-category">{{ item.place.category }}</span>
                        <span v-if="item.place.is_hidden_gem" class="gem-badge" title="Local favorite — high quality, low crowds">
                          <Icon icon="lucide:gem" width="9" height="9" /> Local Gem
                        </span>
                      </div>
                      <h3 class="item-name">{{ item.place.title }}</h3>
                      <p class="item-address" v-if="isReadableAddress(item.place.address)">
                        {{ item.place.address }}
                      </p>
                      <p v-if="item.note" class="item-note">{{ item.note }}</p>
                    </div>
                  </div>

                  <!-- Travel Distance Indicator -->
                  <div v-if="item.distToNext && item.distToNext > 0.05" class="travel-indicator">
                    <Icon icon="lucide:move-right" width="12" height="12" />
                    <span>{{ formatDistance(item.distToNext) }} travel</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </main>
      </aside>

      <!-- Map Pane -->
      <section class="map-pane">
        <div ref="mapContainer" class="map-instance"></div>

        <!-- Route loading badge -->
        <div v-if="routeLoading" class="route-loading-badge">
          <Icon icon="lucide:route" width="12" height="12" />
          Calculating route...
        </div>

        <!-- Floating Overlay Control -->
        <div class="map-controls">
          <button class="control-btn" @click="toggleMap">
            <Icon :icon="isMapFull ? 'lucide:minimize-2' : 'lucide:maximize-2'" width="18" height="18" />
          </button>
        </div>

        <!-- Legend Card -->
        <div class="map-legend nextgen-card">
          <div class="legend-item"><span class="dot bg-primary"></span> Stay</div>
          <div class="legend-item"><span class="dot bg-gold"></span> Dining</div>
          <div class="legend-item"><span class="dot bg-accent"></span> Activity</div>
        </div>
      </section>

    </div>
  </div>
</template>

<style scoped>
.result-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--bg-color);
  position: relative;
}

.overlay-view {
  position: absolute;
  inset: 0;
  z-index: 100;
  background: hsla(var(--background) / 0.8);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.loading-overlay {
  background: hsl(var(--midnight));
  z-index: 1000;
  flex-direction: column;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 500px;
  width: 100%;
}

.lottie-container {
  margin-bottom: 2rem;
  background: white;
  border: 1px solid var(--border-color);
  width: 280px;
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 140px / 160px; /* Vertical Oval */
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
}

.loading-text-wrapper {
  text-align: center;
  margin-bottom: 2rem;
  height: 70px;
}

.loading-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: white;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.loading-subtitle {
  font-size: 0.95rem;
  color: hsla(0, 0%, 100%, 0.6);
  font-weight: 500;
  letter-spacing: 0.02em;
}

.loading-progress-bar {
  width: 200px;
  height: 2px;
  background: hsla(var(--gold) / 0.2);
  border-radius: 0;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 40%;
  background: hsl(var(--gold));
  animation: progress-slide 1.5s infinite cubic-bezier(0.65, 0, 0.35, 1);
}

@keyframes progress-slide {
  0% { left: -40%; }
  100% { left: 100%; }
}

/* Transitions */
.fade-up-enter-active,
.fade-up-leave-active {
  transition: all 0.4s ease;
}

.fade-up-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-up-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.error-box {
  max-width: 400px;
  text-align: center;
  padding: 3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.btn-primary {
  background: hsl(var(--primary));
  color: white;
  padding: 0.75rem 2rem;
  font-size: 0.9375rem;
  font-weight: 700;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: hsl(var(--midnight));
  transform: translateY(-1px);
}

.btn-secondary {
  background: white;
  color: hsl(var(--primary));
  padding: 0.75rem 2rem;
  font-size: 0.9375rem;
  font-weight: 700;
  border-radius: var(--radius);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  border-color: hsl(var(--primary));
  transform: translateY(-1px);
}

/* ── Dashboard Layout ────────────────────────────────────────── */
.dashboard {
  display: flex;
  height: 100%;
  width: 100%;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

/* ── Itinerary Pane ────────────────────────────────────────── */
.itinerary-pane {
  width: 460px;
  background: white;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  min-height: 0;
  overflow: hidden;
  z-index: 10;
  transition: width 0.4s ease, opacity 0.4s ease;
}

.map-expanded .itinerary-pane {
  width: 0;
  opacity: 0;
  border-right: none;
}

.pane-header {
  padding: 1rem 1.25rem;
  background: white;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-group {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.itinerary-title {
  font-size: 1.125rem;
  font-weight: 800;
  color: hsl(var(--primary));
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.meta-item {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.meta-dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--border-color);
}

.header-actions {
  display: flex;
  gap: 0.375rem;
}

.btn-action {
  width: 32px;
  height: 32px;
  border-radius: var(--radius);
  background: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
  color: hsl(var(--primary));
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-action:hover {
  background: hsl(var(--secondary));
  border-color: hsl(var(--primary));
}

/* ── Day Nav ────────────────────────────────────────────────── */
.day-nav {
  padding: 0.5rem 1.5rem;
  background: white;
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 5;
}

.day-scroll {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  padding-bottom: 4px;
}

.day-scroll::-webkit-scrollbar { height: 2px; }

.day-chip {
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-size: 0.8125rem;
  font-weight: 700;
  white-space: nowrap;
  background: white;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.day-chip:hover:not(.active) {
  background: var(--muted);
  border-color: hsl(var(--primary));
  color: hsl(var(--primary));
}

.day-chip.active {
  background: hsl(var(--primary));
  border-color: hsl(var(--primary));
  color: white;
}

/* ── Timeline ───────────────────────────────────────────────── */
.timeline-container {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  background: white;
  scroll-behavior: smooth;
}

.timeline-item {
  display: flex;
  gap: 1.5rem;
  cursor: pointer;
  min-height: 120px;
}

.item-marker {
  width: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.item-time {
  font-size: 0.75rem;
  font-weight: 900;
  color: hsl(var(--primary));
  text-align: right;
  width: 100%;
  margin-top: 10px; /* Align with top of the card/dot */
  line-height: 1.2;
}

.marker-dot {
  width: 32px;
  height: 32px;
  border-radius: var(--radius);
  background: white;
  border: 2px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 4px; /* Align with time label */
  color: hsl(var(--primary));
  z-index: 2;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.marker-line {
  flex: 1;
  width: 2px;
  background: var(--border-color);
  margin: 8px 0;
}

.type-stay .marker-dot { border-color: hsl(var(--primary)); color: white; background: hsl(var(--primary)); }
.type-dining .marker-dot { border-color: hsl(var(--gold)); color: white; background: hsl(var(--gold)); }
.type-activity .marker-dot { border-color: hsl(var(--gold)); color: hsl(var(--primary)); background: hsl(var(--gold)); }

.timeline-item.is-selected .marker-dot {
  transform: scale(1.15);
  box-shadow: 0 0 0 4px hsla(var(--gold) / 0.3);
}

.item-content {
  flex: 1;
  padding-bottom: 2rem;
  min-width: 0;
}

.place-preview {
  display: flex;
  padding: 0;
  overflow: hidden;
  background: white;
  border: 1px solid var(--border-color);
}

.preview-img {
  width: 100px;
  background-size: cover;
  background-position: center;
  background-color: hsl(var(--midnight));
  position: relative;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-img::after {
  content: '';
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23E5A517' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='3' width='18' height='18' rx='2'/%3E%3Ccircle cx='8.5' cy='8.5' r='1.5'/%3E%3Cpath d='m21 15-5-5L5 21'/%3E%3C/svg%3E") center/28px no-repeat;
  opacity: 0.25;
}

.preview-img[style*="background-image"]::after {
  display: none;
}

.rating-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  background: white;
  padding: 2px 4px;
  border-radius: 2px;
  font-size: 0.65rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 2px;
  box-shadow: var(--shadow-sm);
}

.preview-info {
  padding: 0.875rem 1rem;
  flex: 1;
  min-width: 0;
}

.info-tags {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.item-category {
  font-size: 0.65rem;
  text-transform: uppercase;
  font-weight: 700;
  color: hsl(var(--gold));
  letter-spacing: 0.05em;
}

.gem-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 0.6rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #1ABC9C;
  background: hsla(168, 76%, 42%, 0.1);
  padding: 1px 5px;
  border-radius: 2px;
}

.item-name {
  font-size: 0.9375rem;
  font-weight: 800;
  color: hsl(var(--primary));
  margin: 0.125rem 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-address {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-note {
  font-size: 0.75rem;
  font-weight: 700;
  color: hsl(var(--primary));
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.item-note::before {
  content: '';
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: hsl(var(--gold));
}

.travel-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-secondary);
}

/* ── Map Pane ───────────────────────────────────────────────── */
.map-pane {
  flex: 1;
  position: relative;
  min-height: 0;
}

.map-instance {
  width: 100%;
  height: 100%;
}

.route-loading-badge {
  position: absolute;
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 0.375rem 0.875rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: hsl(var(--primary));
  box-shadow: var(--shadow-md);
  z-index: 1000;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.map-controls {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-btn {
  width: 40px;
  height: 40px;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: hsl(var(--primary));
  box-shadow: var(--shadow-lg);
  cursor: pointer;
  transition: background 0.15s;
}

.control-btn:hover {
  background: var(--muted);
}

.map-legend {
  position: absolute;
  bottom: 1.5rem;
  right: 1.5rem;
  z-index: 1000;
  padding: 1rem;
  background: white;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: hsl(var(--primary));
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.bg-primary { background: hsl(var(--primary)); }
.bg-gold { background: hsl(var(--gold)); }
.bg-accent { background: #1ABC9C; }

/* ── Route trail animation ───────────────────────────────────── */
@keyframes route-flow {
  to { stroke-dashoffset: -17; }
}

:deep(.route-trail) {
  animation: route-flow 0.6s linear infinite;
}

/* ── Custom Map Popup ────────────────────────────────────────── */
:deep(.custom-map-popup .leaflet-popup-content-wrapper) {
  padding: 0;
  overflow: hidden;
  border-radius: 4px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--border-color);
}

:deep(.custom-map-popup .leaflet-popup-content) {
  margin: 0;
  padding: 8px 12px;
}

:deep(.custom-map-popup .leaflet-popup-tip) {
  background: white;
  border: 1px solid var(--border-color);
}

/* ── Responsive ─────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .dashboard {
    flex-direction: column;
  }
  .itinerary-pane {
    width: 100%;
    height: 50%;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
  }
}

@media (max-width: 640px) {
  .pane-header { padding: 1rem; }
  .itinerary-title { font-size: 1.25rem; }
  .timeline-container { padding: 1rem; }
}

/* ── Skeleton loading ──────────────────────────────────────── */
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}

.skel {
  background: linear-gradient(90deg, #f0f2f5 25%, #e4e6ea 50%, #f0f2f5 75%);
  background-size: 800px 100%;
  animation: shimmer 1.4s infinite linear;
  border-radius: var(--radius);
}

.skeleton-timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.skeleton-row {
  display: flex;
  gap: 1.5rem;
  min-height: 120px;
}

.skel-marker-col {
  width: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  padding-top: 10px;
}

.skel-time  { width: 48px; height: 14px; margin-bottom: 6px; }
.skel-dot   { width: 32px; height: 32px; border-radius: var(--radius); flex-shrink: 0; }
.skel-line  { flex: 1; width: 2px; margin: 8px 0; border-radius: 0; }

.skel-card {
  flex: 1;
  display: flex;
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  margin-bottom: 2rem;
}

.skel-img   { width: 100px; flex-shrink: 0; }

.skel-info {
  flex: 1;
  padding: 0.875rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.skel-tag   { width: 60px;  height: 10px; }
.skel-title { width: 75%;   height: 16px; }
.skel-addr  { width: 55%;   height: 12px; }

/* Shuffle button spin */
@keyframes spin {
  to { transform: rotate(360deg); }
}

.spin-icon {
  animation: spin 0.8s linear infinite;
}

.btn-action:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
