<script setup>
import { ArrowRight, ArrowLeft, Bed, Coffee } from 'lucide-vue-next'

const props = defineProps({
  accommodation: String,
  dining: String,
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

const setAccom = (val) => emit('update:accommodation', val)
const setDine = (val) => emit('update:dining', val)

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
            class="toggle-card"
            :class="{ active: accommodation === type }"
            @click="setAccom(type)"
          >
            {{ type }}
          </button>
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
            class="toggle-card"
            :class="{ active: dining === type }"
            @click="setDine(type)"
          >
            {{ type }}
          </button>
        </div>
      </div>

      <div v-if="!embedded" class="footer">
        <button class="btn-primary" @click="handleSubmit" :disabled="!accommodation || !dining">
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
  align-items: center;
}

.header-section {
  width: 100%;
  position: relative;
  text-align: center;
  margin-bottom: 2.5rem;
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

h2 {
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

.section-block {
  margin-bottom: 2rem;
}

.block-header {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
}

.icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(229, 165, 23, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 0.75rem;
  color: var(--accent-color);
}

.block-header h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
}

.toggle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
}

.toggle-card {
  padding: 1rem;
  min-height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-align: center;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.toggle-card:hover {
  border-color: var(--text-light);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
  transform: translateY(-2px);
}

.toggle-card.active {
  background: rgba(229, 165, 23, 0.06);
  border: 2px solid var(--accent-color);
  color: var(--primary-color);
  box-shadow: 0 4px 12px rgba(229, 165, 23, 0.15);
  transform: translateY(-2px);
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
  padding-top: 1.5rem;
  margin-top: auto;
  border-top: 1px solid var(--border-color);
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
