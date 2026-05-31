<script setup>
import { computed } from 'vue'
import { ArrowRight, ArrowLeft, CheckCircle2 } from 'lucide-vue-next'

const props = defineProps({
  modelValue: Array,
  availableActivities: {
    type: Array,
    default: () => []
  },
  embedded: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'next', 'back'])

const activities = [
  { id: 'Temple', label: 'Temples & Culture', img: '/img/temple.jpg' },
  { id: 'Museum', label: 'Museums & History', img: '/img/museum.jpg' },
  { id: 'Historical Site', label: 'Historical Sites', img: '/img/historical-site.jpg' },
  { id: 'Landmark', label: 'Landmarks', img: '/img/landmark.jpg' },
  { id: 'Park / Nature', label: 'Parks & Nature', img: '/img/park-and-nature.jpg' },
  { id: 'Beach', label: 'Beaches', img: '/img/beach.jpg' },
  { id: 'Waterfall', label: 'Waterfalls', img: '/img/water-fall.jpg' },
  { id: 'Nightlife / Bars', label: 'Nightlife & Bars', img: '/img/historical-site.jpg' }, // Use fallback images or new ones if available
  { id: 'Coffee & Cafes', label: 'Coffee & Cafes', img: '/img/aquarium.jpg' },
  { id: 'Local Markets', label: 'Local Markets', img: '/img/art-gallary.jpg' },
  { id: 'Aquarium', label: 'Aquariums', img: '/img/aquarium.jpg' },
  { id: 'Art Gallery', label: 'Art Galleries', img: '/img/art-gallary.jpg' },
  { id: 'Wildlife / Zoo', label: 'Wildlife & Zoos', img: '/img/wildlife-zoo.jpg' }
]

const displayedActivities = computed(() => {
  if (props.availableActivities && props.availableActivities.length > 0) {
    return activities.filter(act => props.availableActivities.includes(act.id))
  }
  return [] // Show nothing if no province selected or no activities found
})

const toggleSelection = (id) => {
  const current = [...props.modelValue]
  if (current.includes(id)) {
    emit('update:modelValue', current.filter(item => item !== id))
  } else {
    emit('update:modelValue', [...current, id])
  }
}

const handleNext = () => {
  if (props.modelValue.length > 0) {
    emit('next')
  }
}
</script>

<template>
  <div class="step-container">
    <div v-if="!embedded" class="header-section">
      <button class="back-btn" @click="$emit('back')" title="Go Back">
        <ArrowLeft :size="20" />
      </button>
      <h2>What are your interests?</h2>
      <p class="subtitle">Select the vibes that fit your ideal trip.</p>
    </div>

    <div class="content">
      <div v-if="displayedActivities.length > 0" class="image-grid">
        <div 
          v-for="act in displayedActivities" 
          :key="act.id"
          class="image-card"
          :class="{ 'active': modelValue.includes(act.id) }"
          :style="{ backgroundImage: `url(${act.img})` }"
          @click="toggleSelection(act.id)"
        >
          <div class="card-overlay"></div>
          
          <div class="card-content">
            <span class="card-label">{{ act.label }}</span>
          </div>

          <transition name="scale">
            <div class="check-circle" v-if="modelValue.includes(act.id)">
              <CheckCircle2 :size="24" class="text-white" />
            </div>
          </transition>
        </div>
      </div>

      <div v-else class="no-activities-hint">
        <div class="hint-icon">🔍</div>
        <p v-if="!availableActivities || availableActivities.length === 0">
          Select a destination to see local activities.
        </p>
        <p v-else>
          No specific activities matched our categories in this area.
        </p>
      </div>
      
      <div class="error-msg" v-if="modelValue.length === 0 && displayedActivities.length > 0">
        Please select at least one interest.
      </div>

      <div v-if="!embedded" class="footer">
        <button class="btn-primary" @click="handleNext" :disabled="modelValue.length === 0">
          Continue <ArrowRight :size="20" class="ml-2" />
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
  margin-bottom: 2rem;
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

.header-section h2 {
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

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem; 
  margin-bottom: 1.5rem;
}

.image-card {
  position: relative;
  height: 140px;
  border-radius: var(--radius);
  overflow: hidden;
  background-size: cover;
  background-position: center;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
  border: 2px solid transparent;
}

.image-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: hsla(var(--gold) / 0.4);
}

.image-card.active {
  border-color: hsl(var(--gold));
}

.card-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(to top, hsla(220, 67%, 19%, 0.9) 0%, hsla(220, 67%, 19%, 0.2) 60%);
  transition: opacity 0.3s;
}

.card-content {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  padding: 1.25rem;
  z-index: 2;
}

.card-label {
  color: white;
  font-weight: 700;
  font-size: 0.95rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.check-circle {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  z-index: 3;
  color: hsl(var(--primary));
  background: hsl(var(--gold));
  border-radius: var(--radius);
  display: flex;
  padding: 2px;
}

.text-white { color: currentColor; }

.no-activities-hint {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  background: var(--muted);
  border-radius: var(--radius);
  border: 2px dashed var(--border-color);
  color: var(--text-secondary);
  text-align: center;
}

.hint-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-activities-hint p {
  font-size: 1.1rem;
  font-weight: 500;
  max-width: 300px;
}

.error-msg {
  color: #ef4444;
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 1rem;
  text-align: center;
}

.footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 2rem;
  border-top: 1px solid var(--border-color);
  margin-top: auto;
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
