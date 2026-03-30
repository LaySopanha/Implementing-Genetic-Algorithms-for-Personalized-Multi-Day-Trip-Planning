<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { MapPin, Calendar, Navigation, Search, Map, ChevronDown } from 'lucide-vue-next'
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

const localForm = ref({ ...props.modelValue })

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

const toggleField = (name) => {
  openField.value = openField.value === name ? null : name
}

const selectOption = (field, value) => {
  localForm.value[field] = value
  openField.value = null
  if (field === 'province') destinationError.value = ''
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
const pacingOptions = [
  { value: 1, label: '1 Place/Day (Relaxed)' },
  { value: 2, label: '2 Places/Day (Easy)' },
  { value: 3, label: '3 Places/Day (Normal)' },
  { value: 4, label: '4 Places/Day (Busy)' },
  { value: 5, label: '5 Places/Day (Packed)' },
]
</script>

<template>
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
        @click.stop="toggleField('province')"
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
        <div v-if="openField === 'province'" class="dropdown-list" @click.stop>
          <div
            v-for="prov in provinces"
            :key="prov"
            class="dropdown-item"
            :class="{ selected: localForm.province === prov }"
            @click="selectOption('province', prov)"
          >{{ prov }}</div>
        </div>
      </div>

      <div class="divider"></div>

      <!-- Field 2: Duration -->
      <div
        class="search-field"
        :class="{ 'field-open': openField === 'days' }"
        @click.stop="toggleField('days')"
      >
        <div class="field-content">
          <label>DURATION</label>
          <div class="input-display">
            <Calendar :size="18" class="field-icon" />
            <span class="value-text">{{ localForm.days }} {{ localForm.days === 1 ? 'Day' : 'Days' }}</span>
            <ChevronDown :size="14" class="dropdown-icon" :class="{ rotated: openField === 'days' }" />
          </div>
        </div>
        <div v-if="openField === 'days'" class="dropdown-list" @click.stop>
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

      <!-- Field 3: Pacing -->
      <div
        class="search-field"
        :class="{ 'field-open': openField === 'perDay' }"
        @click.stop="toggleField('perDay')"
      >
        <div class="field-content">
          <label>PACING</label>
          <div class="input-display">
            <Navigation :size="18" class="field-icon" />
            <span class="value-text">{{ localForm.perDay }} Places/Day</span>
            <ChevronDown :size="14" class="dropdown-icon" :class="{ rotated: openField === 'perDay' }" />
          </div>
        </div>
        <div v-if="openField === 'perDay'" class="dropdown-list" @click.stop>
          <div
            v-for="opt in pacingOptions"
            :key="opt.value"
            class="dropdown-item"
            :class="{ selected: localForm.perDay === opt.value }"
            @click="selectOption('perDay', opt.value)"
          >{{ opt.label }}</div>
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
</template>

<style scoped>
.search-bar-wrapper {
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
  position: relative;
  z-index: 30;
  margin-top: -2rem;
}

.search-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0;
  padding-left: 1rem;
}

.tab-btn {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
  border: none;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 12px 12px 0 0;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.35);
}

.tab-btn.active {
  background: white;
  color: var(--primary-color);
}

.search-container {
  background: white;
  border-radius: 16px;
  border-top-left-radius: 0;
  display: flex;
  align-items: stretch;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  padding: 0.75rem;
  border: 1px solid var(--border-color);
}

.search-field {
  flex: 1;
  padding: 0.5rem 1.25rem;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s;
  user-select: none;
}

.search-field:hover,
.search-field.field-open {
  background: var(--bg-color);
}

.field-content {
  display: flex;
  flex-direction: column;
}

.field-content label {
  font-size: 0.65rem;
  font-weight: 800;
  color: var(--text-secondary);
  margin-bottom: 0.2rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.input-display {
  display: flex;
  align-items: center;
  width: 100%;
}

.field-icon {
  color: var(--text-secondary);
  margin-right: 0.5rem;
  flex-shrink: 0;
}

.value-text {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.value-text.placeholder {
  color: var(--text-secondary);
  font-weight: 500;
}

.dropdown-icon {
  color: var(--text-light);
  margin-left: 0.5rem;
  flex-shrink: 0;
  transition: transform 0.2s;
}

.dropdown-icon.rotated {
  transform: rotate(180deg);
}

/* Custom Dropdown */
.dropdown-list {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  min-width: 100%;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 100;
  max-height: 240px;
  overflow-y: auto;
  padding: 0.5rem;
}

.dropdown-list::-webkit-scrollbar {
  width: 4px;
}
.dropdown-list::-webkit-scrollbar-track {
  background: transparent;
}
.dropdown-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

.dropdown-item {
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
}

.dropdown-item:hover {
  background: var(--bg-color);
  color: var(--primary-color);
}

.dropdown-item.selected {
  background: rgba(229, 165, 23, 0.1);
  color: var(--primary-color);
  font-weight: 700;
}

.field-error {
  background: rgba(229, 62, 62, 0.05);
  border-radius: 8px;
}

.error-text {
  color: #e53e3e !important;
  font-weight: 600 !important;
}

.divider {
  width: 1px;
  background: var(--border-color);
  margin: 0.75rem 0;
}

.search-action {
  padding-left: 0.75rem;
  display: flex;
  align-items: stretch;
}

.btn-search {
  background: var(--accent-color);
  color: var(--primary-color);
  border: none;
  border-radius: 12px;
  padding: 0 2.5rem;
  font-size: 1.1rem;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-search:hover {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(229, 165, 23, 0.4);
}

.mr-2 { margin-right: 0.5rem; }

@media (max-width: 900px) {
  .search-container {
    flex-direction: column;
    padding: 1rem;
  }
  .divider {
    width: 100%;
    height: 1px;
    margin: 0.75rem 0;
  }
  .search-field {
    padding: 0.75rem 0.5rem;
  }
  .search-action {
    padding-left: 0;
    margin-top: 1rem;
  }
  .btn-search {
    width: 100%;
    padding: 1rem;
  }
  .tab-btn {
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
  }
  .hidden-mobile {
    display: none;
  }
  .dropdown-list {
    position: fixed;
    top: auto;
    bottom: 0;
    left: 0;
    right: 0;
    min-width: unset;
    width: 100%;
    border-radius: 16px 16px 0 0;
    max-height: 60vh;
  }
}
</style>
