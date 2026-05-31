<script setup>
import { ArrowRight, ArrowLeft, Bed, Coffee } from 'lucide-vue-next'

const props = defineProps({
  accommodation: Array,
  dining: Array,
  availableAccommodation: {
    type: Array,
    default: () => []
  },
  availableDining: {
    type: Array,
    default: () => []
  },
  embedded: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:accommodation', 'update:dining', 'submit', 'back'])

const accommodationTypes = [
  'Hotel', 'Guesthouse', 'Hostel', 'Bed & Breakfast', 'Motel', 'Holiday Park'
]

const diningTypes = [
  'Restaurant', 'Café', 'Fine Dining', 'Casual Dining', 'Food Market / Stall'
]

const toggleAccom = (val) => {
  const current = [...props.accommodation]
  if (current.includes(val)) {
    emit('update:accommodation', current.filter(item => item !== val))
  } else {
    emit('update:accommodation', [...current, val])
  }
}

const toggleDine = (val) => {
  const current = [...props.dining]
  if (current.includes(val)) {
    emit('update:dining', current.filter(item => item !== val))
  } else {
    emit('update:dining', [...current, val])
  }
}

const handleSubmit = () => {
  emit('submit')
}
</script>

<template>
  <div class="step-container">
    <div v-if="!embedded" class="header-section">
      <button class="back-btn" @click="$emit('back')">
        <ArrowLeft :size="20" />
      </button>
      <h2>Where to stay and eat?</h2>
      <p class="subtitle">Customize your accommodation and dining style.</p>
    </div>

    <div class="content">
      
      <div class="section-block">
        <div class="block-header">
          <div class="icon-wrap"><Bed :size="20" /></div>
          <h3>Accommodation</h3>
        </div>
        <div class="toggle-grid">
          <button 
            v-for="type in accommodationTypes" 
            :key="type"
            v-show="availableAccommodation.includes(type)"
            class="toggle-card"
            :class="{ active: accommodation.includes(type) }"
            @click="toggleAccom(type)"
          >
            {{ type }}
          </button>
        </div>
        <div v-if="availableAccommodation.length === 0" class="no-options">
          Select a destination to see stay options.
        </div>
      </div>

      <div class="divider"></div>
      
      <div class="section-block">
        <div class="block-header">
          <div class="icon-wrap"><Coffee :size="20" /></div>
          <h3>Dining Preference</h3>
        </div>
        <div class="toggle-grid">
          <button 
            v-for="type in diningTypes" 
            :key="type"
            v-show="availableDining.includes(type)"
            class="toggle-card"
            :class="{ active: dining.includes(type) }"
            @click="toggleDine(type)"
          >
            {{ type }}
          </button>
        </div>
        <div v-if="availableDining.length === 0" class="no-options">
          Select a destination to see dining options.
        </div>
      </div>

      <div v-if="!embedded" class="footer">
        <button class="btn-primary" @click="handleSubmit" :disabled="accommodation.length === 0 || dining.length === 0">
          Generate Itinerary <ArrowRight :size="20" class="ml-2" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.step-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.header-section {
  width: 100%;
  position: relative;
  text-align: center;
  margin-bottom: 2.5rem;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  border-radius: var(--radius);
  border: 1px solid var(--border-color);
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  color: hsl(var(--primary));
  transition: all 0.2s;
  z-index: 10;
}

.back-btn:hover {
  background: var(--muted);
  border-color: hsl(var(--primary));
}

h2 {
  font-size: 1.75rem;
  font-weight: 800;
  color: hsl(var(--primary));
  margin-bottom: 0.5rem;
  letter-spacing: -0.025em;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
}

.content {
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.section-block {
  margin-bottom: 2rem;
}

.block-header {
  display: flex;
  align-items: center;
  margin-bottom: 1.25rem;
}

.icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: var(--radius);
  background: hsla(var(--gold) / 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 0.75rem;
  color: hsl(var(--gold));
}

.block-header h3 {
  font-size: 1.125rem;
  font-weight: 700;
  color: hsl(var(--primary));
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.toggle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
}

.toggle-card {
  padding: 1.25rem;
  min-height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-align: center;
  transition: all 0.2s ease;
  cursor: pointer;
}

.toggle-card:hover {
  border-color: hsl(var(--primary));
  color: hsl(var(--primary));
}

.toggle-card.active {
  background: hsl(var(--primary));
  border-color: hsl(var(--primary));
  color: white;
  box-shadow: var(--shadow-md);
}

.no-options {
  padding: 1rem;
  background: var(--muted);
  border-radius: var(--radius);
  color: var(--text-secondary);
  font-size: 0.9rem;
  text-align: center;
  border: 1px dashed var(--border-color);
}

.divider {
  height: 1px;
  background: var(--border-color);
  width: 100%;
  margin-bottom: 2rem;
}

.footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 2rem;
  margin-top: auto;
  border-top: 1px solid var(--border-color);
}

.btn-primary {
  background: hsl(var(--primary));
  color: white;
  padding: 0.875rem 2.5rem;
  font-size: 1rem;
  font-weight: 700;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: hsl(var(--midnight));
  transform: translateY(-2px);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--text-light);
}

.ml-2 { margin-left: 0.5rem; }

@media (max-width: 600px) {
  .header-section {
    padding-top: 4rem;
    margin-bottom: 2rem;
  }
  .back-btn {
    top: 0;
    transform: none;
    left: 0;
  }
}
</style>
