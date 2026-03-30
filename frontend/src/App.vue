<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Icon } from '@iconify/vue'
import HeroSearchBar from './components/HeroSearchBar.vue'
import InterestStep from './components/InterestStep.vue'
import StayDineStep from './components/StayDineStep.vue'
import ResultView from './components/ResultView.vue'
import axios from 'axios'

const currentStep = ref(0) // 0: Search form, 4: Result View
const loading = ref(false)
const apiError = ref('')

const isScrolled = ref(false)

const handleScroll = () => {
  isScrolled.value = (window.pageYOffset || document.documentElement.scrollTop) > 20
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

// State — default activities so search works immediately without forcing selection
const formData = ref({
  province: '',
  days: 3,
  perDay: 3,
  activities: ['Temple', 'Museum', 'Landmark'],
  accommodation: 'Hotel',
  dining: 'Restaurant'
})

const itineraryResult = ref(null)

const fetchItinerary = async () => {
  loading.value = true
  apiError.value = ''
  currentStep.value = 4

  try {
    const response = await axios.post('/api/generate-trip', formData.value, { timeout: 30000 })
    itineraryResult.value = response.data
  } catch (error) {
    console.error("Error generating trip:", error)
    if (error.code === 'ECONNABORTED') {
      apiError.value = 'Request timed out. The server is taking too long to respond.'
    } else if (error.response?.data?.detail) {
      apiError.value = error.response.data.detail
    } else {
      apiError.value = 'Could not connect to the server. Please make sure the backend is running.'
    }
  } finally {
    loading.value = false
  }
}

// Restart Trip
const handleRestart = () => {
  currentStep.value = 0
  itineraryResult.value = null
}
</script>

<template>
  <div class="app-container" :class="{ 'result-layout': currentStep === 4 }">
    <!-- Header -->
    <header class="top-header" :class="{ 'header-scrolled': isScrolled }">
      <div class="header-inner">
        <!-- Brand -->
        <div class="header-brand">
          <img src="/nextgen-logo.png" alt="NextGen Logo" class="logo-img" />
          <div class="brand-text">
            <span class="brand-name">Sak Tmor</span>
            <span class="brand-tag">AI Trip Planner · Cambodia</span>
          </div>
        </div>

        <!-- Nav -->
        <nav class="header-nav">
          <a class="nav-link" href="#">Destinations</a>
          <a class="nav-link" href="#">How It Works</a>
          <a class="nav-link" href="#">About</a>
          <button
            v-if="currentStep === 4"
            class="header-cta"
            @click="handleRestart"
          >
            <Icon icon="mdi:plus" width="15" height="15" />
            New Trip
          </button>
        </nav>
      </div>
    </header>

    <!-- Content switches between Search Page & Result Page -->
    <div v-if="currentStep === 0" class="search-page">
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
        @search="fetchItinerary"
      />

      <!-- Preferences always visible below search -->
      <main class="wizard-container mt-8">
        <div class="preferences-card">
          <div class="filters-grid">
            <div class="filter-col">
              <InterestStep
                v-model="formData.activities"
                :embedded="true"
              />
            </div>
            <div class="filter-divider"></div>
            <div class="filter-col">
              <StayDineStep
                v-model:accommodation="formData.accommodation"
                v-model:dining="formData.dining"
                @submit="fetchItinerary"
                :embedded="true"
              />
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- RESULT PAGE -->
    <main v-else-if="currentStep === 4" class="result-page">
      <ResultView :loading="loading" :result="itineraryResult" :error="apiError" @restart="handleRestart" />
    </main>

    <!-- Footer: hidden on result page so the two-panel layout fills the screen -->
    <footer class="app-footer" v-if="currentStep !== 4">
      <div class="footer-inner">

        <!-- Col 1: Brand -->
        <div class="footer-brand">
          <div class="footer-logo-row">
            <img src="/nextgen-logo.png" alt="NextGen" class="footer-logo" />
            <span class="footer-brand-name">Sak Tmor</span>
          </div>
          <p class="footer-tagline">Discover Cambodia through AI-powered travel planning. Build your perfect itinerary in seconds.</p>
          <div class="footer-socials">
            <a href="#" class="social-btn" aria-label="Facebook"><Icon icon="mdi:facebook" width="18" height="18" /></a>
            <a href="#" class="social-btn" aria-label="Instagram"><Icon icon="mdi:instagram" width="18" height="18" /></a>
            <a href="#" class="social-btn" aria-label="Twitter"><Icon icon="mdi:twitter" width="18" height="18" /></a>
          </div>
        </div>

        <!-- Col 2: Explore -->
        <div class="footer-col">
          <h4 class="footer-heading">Explore</h4>
          <ul class="footer-links">
            <li><a href="#">Phnom Penh</a></li>
            <li><a href="#">Siem Reap</a></li>
            <li><a href="#">Sihanoukville</a></li>
            <li><a href="#">Kampot & Kep</a></li>
            <li><a href="#">Battambang</a></li>
          </ul>
        </div>

        <!-- Col 3: Company -->
        <div class="footer-col">
          <h4 class="footer-heading">Company</h4>
          <ul class="footer-links">
            <li><a href="#">About Us</a></li>
            <li><a href="#">How It Works</a></li>
            <li><a href="#">Privacy Policy</a></li>
            <li><a href="#">Terms of Use</a></li>
          </ul>
        </div>

        <!-- Col 4: Contact -->
        <div class="footer-col">
          <h4 class="footer-heading">Contact</h4>
          <ul class="footer-contact">
            <li>
              <Icon icon="mdi:map-marker-outline" width="15" height="15" />
              <span>National Road 6A, Kthor, Prek Leap, Chroy Changvar, Phnom Penh</span>
            </li>
            <li>
              <Icon icon="mdi:email-outline" width="15" height="15" />
              <span>hello@nextgen.edu.kh</span>
            </li>
            <li>
              <Icon icon="mdi:web" width="15" height="15" />
              <span>www.nextgen.edu.kh</span>
            </li>
          </ul>
        </div>

      </div>

      <!-- Bottom bar -->
      <div class="footer-bottom">
        <p>&copy; 2026 NextGen. All Rights Reserved.</p>
        <p>Built with <Icon icon="mdi:heart" width="13" height="13" style="color:#E5A517;vertical-align:middle" /> by NextGen Students</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
  width: 100%;
}

/* In result mode: lock to exact viewport height so nothing overflows */
.app-container.result-layout {
  height: 100vh;
  overflow: hidden;
}

/* ── Header ──────────────────────────────────────────────────────────────── */
.top-header {
  background-color: var(--surface-color);
  width: 100%;
  padding: 0 var(--spacing-container);
  z-index: 100;
  position: sticky;
  top: 0;
  flex-shrink: 0;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  border-bottom: 1px solid transparent;
}

.top-header.header-scrolled {
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom-color: rgba(0, 0, 0, 0.05);
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.03);
}

.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
  transition: height 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.top-header.header-scrolled .header-inner {
  height: 60px;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  flex-shrink: 0;
}

.logo-img {
  height: 36px;
  width: auto;
  object-fit: contain;
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 0;
  border-left: 1.5px solid var(--border-color);
  padding-left: 0.75rem;
}

.brand-name {
  font-size: 1rem;
  font-weight: 800;
  color: var(--primary-color);
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.brand-tag {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.nav-link {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 0.4rem 0.75rem;
  border-radius: var(--radius-md);
  text-decoration: none;
  transition: color 0.15s, background 0.15s;
}

.nav-link:hover {
  color: var(--primary-color);
  background: var(--bg-color);
}

.header-cta {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--accent-color);
  color: var(--primary-color);
  font-size: 0.85rem;
  font-weight: 800;
  padding: 0.45rem 1rem;
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  margin-left: 0.5rem;
  transition: background 0.15s, transform 0.15s;
}

.header-cta:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

.search-page {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.hero-banner {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
  color: var(--text-inverse);
  padding: 2.5rem var(--spacing-container) 4rem var(--spacing-container);
  text-align: center;
  position: relative;
}

.hero-banner::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: radial-gradient(circle at 50% 100%, rgba(229, 165, 23, 0.08) 0%, transparent 60%);
  pointer-events: none;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  z-index: 10;
}

.khmer-title {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: var(--accent-color);
  letter-spacing: 0.05em;
}

.main-title {
  font-size: 2.2rem;
  font-weight: 800;
  margin-bottom: 0.75rem;
  line-height: 1.2;
}

.subtitle {
  font-size: 1rem;
  opacity: 0.9;
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
  margin-bottom: 3rem;
  z-index: 20;
  width: 100%;
}

.result-page {
  flex: 1;
  min-height: 0;   /* allows flex child to shrink below content size */
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* PREFERENCES CARD — always visible below search */
.preferences-card {
  background-color: var(--surface-color);
  width: 100%;
  max-width: 1000px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: 2rem 2.5rem;
  border: 1px solid var(--border-color);
}

.filters-grid {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.filter-col {
  flex: 1;
}

.filter-divider {
  height: 1px;
  width: 100%;
  background: var(--border-color);
}

/* WIZARD CARD (Used solely for ResultView now) */
.wizard-card {
  background-color: var(--surface-color);
  width: 100%;
  max-width: 1280px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
}

.wizard-card.result-mode {
  padding: 0;
  overflow: hidden;
}

/* ── Footer ──────────────────────────────────────────────────────────────── */
.app-footer {
  background-color: var(--midnight);
  color: var(--text-inverse);
  padding: 4rem var(--spacing-container) 2rem var(--spacing-container);
  margin-top: auto;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.footer-inner {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1.5fr;
  gap: 3rem;
  margin-bottom: 3rem;
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.footer-logo-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.footer-logo {
  height: 32px;
  width: auto;
}

.footer-brand-name {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--accent-color);
  letter-spacing: -0.02em;
}

.footer-tagline {
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--text-light);
  max-width: 320px;
}

.footer-socials {
  display: flex;
  gap: 0.75rem;
}

.social-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-inverse);
  transition: all 0.2s;
}

.social-btn:hover {
  background: var(--accent-color);
  color: var(--primary-color);
  transform: translateY(-3px);
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.footer-heading {
  font-size: 0.9rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--surface-color);
}

.footer-links {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.footer-links a {
  font-size: 0.9rem;
  color: var(--text-light);
  transition: color 0.15s;
}

.footer-links a:hover {
  color: var(--accent-color);
}

.footer-contact {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.footer-contact li {
  display: flex;
  gap: 0.75rem;
  font-size: 0.85rem;
  color: var(--text-light);
  line-height: 1.5;
}

.footer-contact li .iconify {
  flex-shrink: 0;
  color: var(--accent-color);
  margin-top: 0.2rem;
}

.footer-bottom {
  max-width: 1280px;
  margin: 0 auto;
  padding-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.footer-bottom p {
  font-size: 0.8rem;
  color: var(--text-light);
}

@media (max-width: 1024px) {
  .footer-inner {
    grid-template-columns: 1fr 1fr;
    gap: 2.5rem;
  }
}

@media (max-width: 640px) {
  .footer-inner {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  .footer-bottom {
    flex-direction: column;
    text-align: center;
  }
}

@media (max-width: 768px) {
  .preferences-card { padding: 1.5rem 1rem; }
  .filters-grid { gap: 1.5rem; }
  .main-title { font-size: 1.5rem; }
  .hero-banner { padding: 1.5rem 1rem 3rem 1rem; }
}
</style>
