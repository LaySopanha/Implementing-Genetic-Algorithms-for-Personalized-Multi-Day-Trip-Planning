<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import HeroSearchBar from '../components/HeroSearchBar.vue'
import InterestStep from '../components/InterestStep.vue'
import StayDineStep from '../components/StayDineStep.vue'
import axios from 'axios'

const router = useRouter()

// State — default activities
const formData = ref({
  province: '',
  days: 3,
  perDay: 3,
  activities: ['Temple', 'Museum', 'Landmark'],
  accommodation: ['Hotel'],
  dining: ['Restaurant']
})

const availableFilters = ref({
  activities: [],
  accommodation: [],
  dining: []
})
const loadingFilters = ref(false)

watch(() => formData.value.province, async (newProv) => {
  if (!newProv) {
    availableFilters.value = { activities: [], accommodation: [], dining: [] }
    return
  }
  
  loadingFilters.value = true
  try {
    const res = await axios.get(`/api/activities/${newProv}`)
    if (res.data) {
      availableFilters.value = {
        activities: res.data.activities || [],
        accommodation: res.data.accommodation || [],
        dining: res.data.dining || []
      }
      
      // Auto-prune selections that are no longer available in the new province
      formData.value.activities = formData.value.activities.filter(act => 
        availableFilters.value.activities.includes(act)
      )
      formData.value.accommodation = formData.value.accommodation.filter(acc => 
        availableFilters.value.accommodation.includes(acc)
      )
      formData.value.dining = formData.value.dining.filter(dine => 
        availableFilters.value.dining.includes(dine)
      )
      
      // Ensure at least one selection if list becomes empty but options exist
      if (formData.value.activities.length === 0 && availableFilters.value.activities.length > 0) {
        formData.value.activities.push(availableFilters.value.activities[0])
      }
      if (formData.value.accommodation.length === 0 && availableFilters.value.accommodation.length > 0) {
        formData.value.accommodation.push(availableFilters.value.accommodation[0])
      }
      if (formData.value.dining.length === 0 && availableFilters.value.dining.length > 0) {
        formData.value.dining.push(availableFilters.value.dining[0])
      }
    }
  } catch (err) {
    console.error("Error fetching available filters for province:", err)
    availableFilters.value = { activities: [], accommodation: [], dining: [] }
  } finally {
    loadingFilters.value = false
  }
})

const goToItinerary = () => {
  if (!formData.value.province) return

  // Navigate to itinerary route with query params
  router.push({
    name: 'itinerary',
    query: {
      province: formData.value.province,
      days: formData.value.days,
      perDay: formData.value.perDay,
      activities: formData.value.activities,
      accommodation: formData.value.accommodation,
      dining: formData.value.dining
    }
  })
}
</script>

<template>
  <div class="home-view">
    <!-- Search Page Content -->
    <div class="search-page">
      <!-- Hero Banner -->
      <section class="hero-banner">
        <div class="hero-content">
          <h2 class="khmer-title khmer">កម្មវិធីរៀបចំផែនការធ្វើដំណើរ</h2>
          <h1 class="main-title">Automating Your Trip Planning Experience</h1>
          <p class="subtitle">Tell us your preferences and get an instant AI-generated itinerary</p>
        </div>
      </section>

      <!-- The New Search Bar Floating Over Hero -->
      <HeroSearchBar
        v-model="formData"
        @search="goToItinerary"
      />

      <!-- Preferences always visible below search -->
      <main class="wizard-container mt-8">
        <div class="preferences-card nextgen-card" :class="{ 'is-loading': loadingFilters }">
          <div v-if="loadingFilters" class="loading-overlay">
            <div class="spinner"></div>
            <p>Fetching local vibes...</p>
          </div>
          
          <div class="filters-grid">
            <div class="filter-col">
              <InterestStep
                v-model="formData.activities"
                :availableActivities="availableFilters.activities"
                :embedded="true"
              />
            </div>
            <div class="filter-divider"></div>
            <div class="filter-col">
              <StayDineStep
                v-model:accommodation="formData.accommodation"
                v-model:dining="formData.dining"
                :availableAccommodation="availableFilters.accommodation"
                :availableDining="availableFilters.dining"
                @submit="goToItinerary"
                :embedded="true"
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.home-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.search-page {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.hero-banner {
  color: white;
  padding: 10rem var(--spacing-container) 10rem var(--spacing-container);
  text-align: center;
  position: relative;
  background-image: url('/hero.jpg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
}
/* ... rest of styles remain similar, removing result-layout related ones ... */
.hero-banner::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, 
    hsl(var(--midnight) / 0.8) 0%, 
    hsl(var(--midnight) / 0.4) 50%,
    hsl(var(--midnight) / 0.9) 100%
  );
  z-index: 1;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  z-index: 10;
}

.khmer-title {
  font-size: 1.1rem;
  font-weight: 500;
  margin-bottom: 0.75rem;
  color: hsl(var(--gold));
  letter-spacing: 0.05em;
}

.main-title {
  font-size: 3rem;
  font-weight: 900;
  margin-bottom: 1rem;
  line-height: 1.1;
  letter-spacing: -0.04em;
}

.subtitle {
  font-size: 1.125rem;
  opacity: 0.8;
  font-weight: 400;
  max-width: 600px;
  margin: 0 auto;
}

.mt-8 {
  margin-top: 2rem;
}

.wizard-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 var(--spacing-container);
  margin-bottom: 4rem;
  z-index: 20;
  width: 100%;
}

.preferences-card {
  width: 100%;
  max-width: 1100px;
  padding: 2.5rem;
  background: white;
  position: relative;
}

.preferences-card.is-loading {
  opacity: 0.7;
  pointer-events: none;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.6);
  z-index: 50;
  border-radius: var(--radius);
}

.loading-overlay p {
  margin-top: 1rem;
  font-weight: 600;
  color: hsl(var(--primary));
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid hsla(var(--gold) / 0.2);
  border-top-color: hsl(var(--gold));
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.filters-grid {
  display: flex;
  flex-direction: row;
  gap: 3rem;
}

.filter-col {
  flex: 1;
}

.filter-divider {
  width: 1px;
  background: var(--border-color);
}

@media (max-width: 900px) {
  .filters-grid {
    flex-direction: column;
  }
  .filter-divider {
    height: 1px;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .main-title { font-size: 2rem; }
  .hero-banner { padding: 3rem 1rem 5rem 1rem; }
}
</style>
