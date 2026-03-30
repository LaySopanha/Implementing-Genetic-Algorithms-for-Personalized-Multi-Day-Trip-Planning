<script setup>
import { ArrowRight, ArrowLeft, CheckCircle2 } from 'lucide-vue-next'

const props = defineProps({
  modelValue: Array,
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
  { id: 'Aquarium', label: 'Aquariums', img: '/img/aquarium.jpg' },
  { id: 'Art Gallery', label: 'Art Galleries', img: '/img/art-gallary.jpg' },
  { id: 'Wildlife / Zoo', label: 'Wildlife & Zoos', img: '/img/wildlife-zoo.jpg' }
]

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
      <div class="image-grid">
        <div 
          v-for="act in activities" 
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
      
      <div class="error-msg" v-if="modelValue.length === 0">
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
  align-items: center;
}

.header-section {
  width: 100%;
  position: relative;
  text-align: center;
  margin-bottom: 2rem;
  animation: fadeInDown 0.4s ease-out forwards;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  transition: all 0.2s;
  z-index: 10;
}

.back-btn:hover {
  background: var(--bg-color);
  border-color: var(--text-secondary);
  color: var(--primary-color);
}

.header-section h2 {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--primary-color);
  margin-bottom: 0.25rem;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
}

.content {
  width: 100%;
  animation: fadeIn 0.5s ease-out forwards;
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
  height: 130px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background-size: cover;
  background-position: center;
  cursor: pointer;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s ease;
  box-shadow: var(--shadow-sm);
  border: 3px solid transparent;
}

.image-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.image-card.active {
  transform: scale(0.97);
  border-color: var(--accent-color);
  box-shadow: 0 0 0 4px rgba(229, 165, 23, 0.2);
}

.card-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(to top, rgba(16,32,80,0.9) 0%, rgba(16,32,80,0.2) 60%);
  transition: opacity 0.3s;
}

.image-card.active .card-overlay {
  background: rgba(16,32,80,0.6);
}

.card-content {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  padding: 1rem;
  z-index: 2;
}

.card-label {
  color: white;
  font-weight: 700;
  font-size: 1rem;
  text-shadow: 0 2px 4px rgba(0,0,0,0.8);
}

.check-circle {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  z-index: 3;
  color: var(--accent-color);
  background: white; /* Make the icon pop against images */
  border-radius: 50%;
  display: flex;
}

.text-white { color: currentColor; } /* Inherits from parent wrapper now */

/* Scale Transition */
.scale-enter-active,
.scale-leave-active {
  transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.scale-enter-from,
.scale-leave-to {
  opacity: 0;
  transform: scale(0.5);
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
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-color);
  margin-top: auto;
}

.btn-primary {
  background: var(--accent-color); /* NextGen Gold */
  color: var(--primary-color);
  padding: 0.8rem 2rem;
  font-size: 1rem;
  font-weight: 700;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--text-light);
  color: white;
}

.ml-2 { margin-left: 0.5rem; }

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (max-width: 600px) {
  .header-section {
    display: flex;
    flex-direction: column;
    padding-top: 3.5rem; /* Make room for absolute back button */
    margin-bottom: 2rem;
  }
  .back-btn {
    top: 0;
    transform: none;
    left: 0;
  }
}
</style>
