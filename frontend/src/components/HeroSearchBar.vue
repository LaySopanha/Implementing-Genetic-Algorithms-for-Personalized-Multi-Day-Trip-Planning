<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { MapPin, Calendar, Compass, Search, Map, ChevronDown } from 'lucide-vue-next'
import axios from 'axios'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'search'])

const provinces = ref([])
const loadingProvinces = ref(false)
const destinationError = ref('')
const openField = ref(null)
const dropUp = ref(false)
const provinceQuery = ref('')
const provinceInput = ref(null)

const localForm = ref({ ...props.modelValue })
const filteredProvinces = computed(() => {
  const q = provinceQuery.value.toLowerCase().trim()
  if (!q) return provinces.value

  // 1. Priority: Substring matches
  const substringMatches = provinces.value.filter(p => p.toLowerCase().includes(q))
  if (substringMatches.length > 0) {
    // If we have an exact match or very strong substring match, just show those
    return substringMatches
  }

  // 2. Fallback: Fuzzy matching for typos (Levenshtein distance)
  return provinces.value.filter(p => {
    const name = p.toLowerCase()
    return levenshtein(q, name) <= 2 // Allow up to 2 edits for longer strings
  })
})

// Simple Levenshtein distance for typo detection
const levenshtein = (a, b) => {
  const matrix = []
  for (let i = 0; i <= b.length; i++) matrix[i] = [i]
  for (let j = 0; j <= a.length; j++) matrix[0][j] = j

  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1]
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        )
      }
    }
  }
  return matrix[b.length][a.length]
}

const highlightMatch = (text, query) => {
  if (!query) return text
  const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escapedQuery})`, 'gi')
  return text.replace(regex, '<span class="match-highlight">$1</span>')
}

onMounted(async () => {
  loadingProvinces.value = true
  try {
    const res = await axios.get('/api/provinces')
    if (res.data && res.data.provinces) {
      provinces.value = res.data.provinces
    } else {
      provinces.value = ['Phnom Penh', 'Siem Reap', 'Preah Sihanouk', 'Kampot', 'Kep', 'Battambang']
    }
  } catch (err) {
    console.error("Error loading provinces", err)
    provinces.value = ['Phnom Penh', 'Siem Reap', 'Preah Sihanouk', 'Kampot', 'Battambang']
  } finally {
    loadingProvinces.value = false
  }

  document.addEventListener('click', closeAll)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', closeAll)
})

const updateForm = () => {
  emit('update:modelValue', localForm.value)
}

const toggleField = (name, event) => {
  if (openField.value === name) {
    openField.value = null
    return
  }

  // Smart positioning: check if there's enough space below
  if (event && event.currentTarget) {
    const rect = event.currentTarget.getBoundingClientRect()
    const spaceBelow = window.innerHeight - rect.bottom
    const dropdownHeight = 300 // max-height 280px + buffer
    dropUp.value = spaceBelow < dropdownHeight
  }

  openField.value = name

  if (name === 'province') {
    provinceQuery.value = '' // Clear for fresh search inside dropdown
    nextTick(() => {
      provinceInput.value?.focus()
    })
  }
}

const selectOption = (field, value) => {
  localForm.value[field] = value
  openField.value = null
  if (field === 'province') {
    destinationError.value = ''
    provinceQuery.value = value
  }
  updateForm()
}

const closeAll = () => {
  openField.value = null
}

const handleSearch = () => {
  if (!localForm.value.province) {
    destinationError.value = 'Please select a destination first.'
    return
  }
  destinationError.value = ''
  emit('update:modelValue', localForm.value)
  emit('search')
}

const durationOptions = Array.from({ length: 14 }, (_, i) => i + 1)
const tripStyleOptions = [
  { value: 'adventure', label: 'Adventure', desc: 'New area & hotel daily, more stops' },
  { value: 'balanced',  label: 'Balanced',  desc: 'Comfortable mix of sights and rest' },
  { value: 'chill',     label: 'Chill',     desc: 'One base, slow pace, fewer stops' },
]
const currentStyleLabel = computed(() =>
  tripStyleOptions.find(o => o.value === localForm.value.mode)?.label || 'Balanced'
)
</script>
<template>
  <div class="hero-search-root">
    <!-- Backdrop overlay -->
    <Transition name="fade">
      <div v-if="openField" class="search-backdrop" @click="closeAll"></div>
    </Transition>

    <div class="search-bar-wrapper">
      <!-- Top Tab -->
      <div class="search-tabs">
        <button class="tab-btn active">
          <Map :size="18" class="mr-2" /> Trip Planner
        </button>
      </div>

    <!-- Main Search Container -->
    <div class="search-container">

      <!-- Field 1: Destination -->
      <div
        class="search-field destination-field"
        :class="{ 'field-error': destinationError, 'field-open': openField === 'province' }"
        @click.stop="toggleField('province', $event)"
      >
        <div class="field-content">
          <label>DESTINATION</label>
          <div class="input-display">
            <MapPin :size="18" class="field-icon" />
            <span class="value-text" :class="{ placeholder: !localForm.province, 'error-text': destinationError && !localForm.province }">
              {{ localForm.province || (destinationError ? destinationError : 'Where are you going?') }}
            </span>
            <ChevronDown :size="14" class="dropdown-icon" :class="{ rotated: openField === 'province' }" />
          </div>
        </div>
        <div v-if="openField === 'province'" class="dropdown-list" :class="{ 'is-drop-up': dropUp }" @click.stop>
          <div class="dropdown-search-wrapper" @click.stop>
            <Search :size="14" class="search-icon" />
            <input
              ref="provinceInput"
              v-model="provinceQuery"
              class="dropdown-search-input"
              placeholder="Search province"
              @keyup.enter="filteredProvinces.length > 0 && selectOption('province', filteredProvinces[0])"
            />
          </div>
          <div
            v-for="prov in filteredProvinces"
            :key="prov"
            class="dropdown-item"
            :class="{ selected: localForm.province === prov }"
            @click="selectOption('province', prov)"
            v-html="highlightMatch(prov, provinceQuery)"
          ></div>
          <div v-if="filteredProvinces.length === 0" class="no-results">
            No matches found
          </div>
        </div>
      </div>

      <div class="divider"></div>

      <!-- Field 2: Duration -->
      <div
        class="search-field"
        :class="{ 'field-open': openField === 'days' }"
        @click.stop="toggleField('days', $event)"
      >
        <div class="field-content">
          <label>DURATION</label>
          <div class="input-display">
            <Calendar :size="18" class="field-icon" />
            <span class="value-text">{{ localForm.days }} {{ localForm.days === 1 ? 'Day' : 'Days' }}</span>
            <ChevronDown :size="14" class="dropdown-icon" :class="{ rotated: openField === 'days' }" />
          </div>
        </div>
        <div v-if="openField === 'days'" class="dropdown-list" :class="{ 'is-drop-up': dropUp }" @click.stop>
          <div
            v-for="n in durationOptions"
            :key="n"
            class="dropdown-item"
            :class="{ selected: localForm.days === n }"
            @click="selectOption('days', n)"
          >{{ n }} {{ n === 1 ? 'Day' : 'Days' }}</div>
        </div>
      </div>

      <div class="divider"></div>

      <!-- Field 3: Trip Style -->
      <div
        class="search-field"
        :class="{ 'field-open': openField === 'mode' }"
        @click.stop="toggleField('mode', $event)"
      >
        <div class="field-content">
          <label>TRIP STYLE</label>
          <div class="input-display">
            <Compass :size="18" class="field-icon" />
            <span class="value-text">{{ currentStyleLabel }}</span>
            <ChevronDown :size="14" class="dropdown-icon" :class="{ rotated: openField === 'mode' }" />
          </div>
        </div>
        <div v-if="openField === 'mode'" class="dropdown-list" :class="{ 'is-drop-up': dropUp }" @click.stop>
          <div
            v-for="opt in tripStyleOptions"
            :key="opt.value"
            class="dropdown-item style-item"
            :class="{ selected: localForm.mode === opt.value }"
            @click="selectOption('mode', opt.value)"
          >
            <span class="style-item-label">{{ opt.label }}</span>
            <span class="style-item-desc">{{ opt.desc }}</span>
          </div>
        </div>
      </div>

      <!-- Search Button -->
      <div class="search-action">
        <button class="btn-search" @click="handleSearch">
          <Search :size="20" class="mr-2 hidden-mobile" /> Search
        </button>
      </div>

    </div>
  </div>
</div>
</template>
<style scoped>
.hero-search-root {
  width: 100%;
  display: flex;
  justify-content: center;
  position: relative;
}

.search-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.25); /* Lighter backdrop */
  backdrop-filter: blur(4px); /* Toned down from 8px */
  -webkit-backdrop-filter: blur(4px);
  z-index: 990;
  cursor: pointer;
}

.search-bar-wrapper {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  position: relative;
  z-index: 1001;
  margin-top: -2.5rem;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.search-tabs {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 0;
}

.tab-btn {
  display: flex;
  align-items: center;
  background: rgba(16, 32, 80, 0.6); /* Slightly more solid, less translucent */
  border: none;
  color: white;
  padding: 0.875rem 2rem;
  border-radius: var(--radius) var(--radius) 0 0;
  font-weight: 700;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: rgba(16, 32, 80, 0.8);
}

.tab-btn.active {
  background: white;
  color: hsl(var(--primary));
}

.search-container {
  background: white;
  border-radius: var(--radius);
  border-top-left-radius: 0;
  display: flex;
  align-items: stretch;
  box-shadow: var(--shadow-lg);
  padding: 0.5rem;
  border: 1px solid var(--border-color);
}

.search-field {
  flex: 1;
  padding: 0.75rem 1.5rem;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  cursor: pointer;
  border-radius: var(--radius);
  transition: background 0.2s;
  user-select: none;
}

.search-field:hover,
.search-field.field-open {
  background: var(--muted);
}

.field-content {
  display: flex;
  flex-direction: column;
}

.field-content label {
  font-size: 0.7rem;
  font-weight: 700;
  color: hsl(var(--gold));
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.input-display {
  display: flex;
  align-items: center;
  width: 100%;
}

.field-icon {
  color: hsl(var(--primary));
  margin-right: 0.75rem;
  flex-shrink: 0;
  opacity: 0.8;
}

.value-text {
  font-size: 1rem;
  font-weight: 600;
  color: hsl(var(--primary));
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.01em;
}

.value-text.placeholder {
  color: var(--text-secondary);
  font-weight: 400;
}

.dropdown-icon {
  color: var(--text-secondary);
  margin-left: 0.75rem;
  flex-shrink: 0;
  transition: transform 0.2s;
}

.dropdown-icon.rotated {
  transform: rotate(180deg);
}

/* Custom Dropdown */
.dropdown-list {
  position: absolute;
  top: calc(100% + 12px); /* Increased gap to clear container padding and border */
  left: 0;
  width: 100%;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  z-index: 100;
  max-height: 320px;
  overflow-y: auto;
  padding: 0.25rem;
}

.dropdown-list.is-drop-up {
  top: auto;
  bottom: calc(100% + 12px);
}

/* Ensure destination dropdown aligns with the very left of the container */
.destination-field .dropdown-list {
  left: -0.5rem;
  width: calc(100% + 0.5rem);
  border-top-left-radius: 0;
  border-bottom-left-radius: var(--radius);
}

.dropdown-search-wrapper {
  position: sticky;
  top: -0.25rem;
  background: white;
  z-index: 10;
  padding: 0.75rem 1rem 0.75rem 1.5rem; /* Aligned with field padding */
  margin: -0.25rem -0.25rem 0.25rem -0.25rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.search-icon {
  color: var(--text-secondary);
  opacity: 0.6;
  margin-left: 0.15rem; /* Micro-adjustment to align with MapPin */
}

.dropdown-search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 0.95rem;
  font-weight: 500;
  color: hsl(var(--primary));
  background: transparent;
  width: 100%;
}

.dropdown-search-input::placeholder {
  color: var(--text-secondary);
  opacity: 0.5;
}

.dropdown-item {
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius);
  font-size: 0.95rem;
  font-weight: 500;
  color: hsl(var(--primary));
  cursor: pointer;
  transition: all 0.2s;
  text-align: left; /* Explicitly left-aligned */
  display: block;
  width: 100%;
}

.dropdown-item:hover {
  background: var(--muted); /* More visible hover state */
  color: hsl(var(--gold));
}

.dropdown-item.selected {
  background: hsl(var(--primary));
  color: white;
}

/* Trip-style two-line items */
.style-item {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.style-item-label {
  font-weight: 700;
}

.style-item-desc {
  font-size: 0.78rem;
  font-weight: 400;
  color: var(--text-secondary);
}

.dropdown-item.selected .style-item-desc {
  color: hsla(0, 0%, 100%, 0.75);
}

.no-results {
  padding: 1rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
  text-align: center;
}

/* Match highlighting */
:deep(.match-highlight) {
  color: hsl(var(--gold));
  font-weight: 800;
}

.selected :deep(.match-highlight) {
  color: white;
}

.field-error {
  border: 1px solid hsla(0, 100%, 50%, 0.2);
  background: hsla(0, 100%, 50%, 0.02);
}

.error-text {
  color: #ef4444 !important;
}

.divider {
  width: 1px;
  background: var(--border-color);
  margin: 1rem 0;
}

.search-action {
  padding-left: 0.5rem;
  display: flex;
  align-items: stretch;
}

.btn-search {
  background: hsl(43 82% 49%); /* Solid color, no gradient */
  color: hsl(var(--primary));
  border: none;
  border-radius: var(--radius);
  padding: 0 3rem;
  font-size: 1rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-search:hover {
  background: hsl(43 82% 55%); /* Subtle solid color change */
  transform: translateY(-1px);
}

.mr-2 { margin-right: 0.5rem; }

@media (max-width: 640px) {
  .hidden-mobile { display: none; }
}

@media (max-width: 900px) {
  .search-container {
    flex-direction: column;
    padding: 1rem;
  }
  .divider {
    width: 100%;
    height: 1px;
    margin: 0.5rem 0;
  }
  .search-field {
    padding: 1rem;
  }
  .search-action {
    padding-left: 0;
    margin-top: 1rem;
  }
  .btn-search {
    width: 100%;
    padding: 1.25rem;
  }
}
</style>
