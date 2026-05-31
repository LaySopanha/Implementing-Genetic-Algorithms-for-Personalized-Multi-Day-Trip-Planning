<script setup>
import { ref, onMounted, onUnmounted, provide, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Icon } from '@iconify/vue'

const route = useRoute()
const isScrolled = ref(false)
const isHidden = ref(false)
let lastScrollY = 0

const isHome = computed(() => route.path === '/')
const isResultMode = computed(() => route.path === '/itinerary')

// Provide this to children if they still need it (like for manual overrides), 
// but most should now rely on the route.
provide('setResultMode', (val) => {
  // Manual override if absolutely necessary, but preferred to use route
})

// CRITICAL: Reset hidden state whenever the route changes.
watch(() => route.path, () => {
  isHidden.value = false
})

const handleScroll = () => {
  const currentScrollY = window.pageYOffset || document.documentElement.scrollTop
  
  // Show/Hide logic: Hide when scrolling down, show when scrolling up
  if (currentScrollY > lastScrollY && currentScrollY > 150) {
    isHidden.value = true
  } else {
    isHidden.value = false
  }
  
  isScrolled.value = currentScrollY > 20
  lastScrollY = currentScrollY
}

const handleInternalScroll = (e) => {
  const currentScrollY = e.detail.scrollTop
  
  if (currentScrollY > lastScrollY && currentScrollY > 100) {
    isHidden.value = true
  } else {
    isHidden.value = false
  }
  
  isScrolled.value = currentScrollY > 20
  lastScrollY = currentScrollY
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  window.addEventListener('internal-scroll', handleInternalScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('internal-scroll', handleInternalScroll)
})
</script>

<template>
  <div class="app-container" :class="{ 'is-result-mode': isResultMode }">
    <!-- Header -->
    <header 
      class="top-header" 
      :class="{ 
        'header-scrolled': isScrolled,
        'header-transparent': isHome && !isScrolled && !isResultMode,
        'header-hidden': isHidden
      }"
    >
      <div class="header-inner">
        <!-- Brand -->
        <router-link to="/" class="header-brand">
          <img src="/nextgen-logo.png" alt="NextGen Logo" class="logo-img" />
          <div class="brand-text">
            <span class="brand-name">Sak Tmor</span>
            <span class="brand-tag">AI Trip Planner · Cambodia</span>
          </div>
        </router-link>

        <!-- Nav -->
        <nav class="header-nav">
          <router-link class="nav-link" to="/">Home</router-link>
          <router-link class="nav-link" to="/destinations">Destinations</router-link>
          <router-link class="nav-link" to="/how-it-works">How It Works</router-link>
          <router-link class="nav-link" to="/about">About</router-link>
          <router-link
            v-if="!isResultMode"
            to="/"
            class="header-cta bg-gold-gradient"
          >
            <Icon icon="lucide:plus" width="16" height="16" />
            Plan Trip
          </router-link>
        </nav>
      </div>
    </header>

    <!-- Content -->
    <main class="main-content" :class="{ 'is-home-page': isHome, 'is-result-mode': isResultMode }">
      <router-view />
    </main>

    <!-- Footer -->
    <footer v-if="!isResultMode" class="app-footer bg-royal-gradient">
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
            <li><router-link to="/destinations">Phnom Penh</router-link></li>
            <li><router-link to="/destinations">Siem Reap</router-link></li>
            <li><router-link to="/destinations">Sihanoukville</router-link></li>
            <li><router-link to="/destinations">Kampot & Kep</router-link></li>
            <li><router-link to="/destinations">Battambang</router-link></li>
          </ul>
        </div>

        <!-- Col 3: Company -->
        <div class="footer-col">
          <h4 class="footer-heading">Company</h4>
          <ul class="footer-links">
            <li><router-link to="/about">About Us</router-link></li>
            <li><router-link to="/how-it-works">How It Works</router-link></li>
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
        <p>Built with <Icon icon="mdi:heart" width="13" height="13" style="color:hsl(var(--gold));vertical-align:middle" /> by NextGen Students</p>
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

/* Only lock the screen when in result mode */
.app-container.is-result-mode {
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding-top: 72px; /* Header height */
}

.main-content.is-home-page {
  padding-top: 0;
}

.is-result-mode .main-content {
  min-height: 0;
}

/* ── Header ──────────────────────────────────────────────────────────────── */
.top-header {
  background-color: hsl(var(--midnight));
  width: 100%;
  padding: 0 var(--spacing-container);
  z-index: 1000;
  position: fixed;
  top: 0;
  left: 0;
  flex-shrink: 0;
  height: 72px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.header-transparent {
  background-color: transparent;
  border-bottom-color: transparent;
}

.header-scrolled {
  background-color: hsl(var(--midnight) / 0.98);
  backdrop-filter: blur(15px);
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
  height: 64px;
}

.header-hidden {
  transform: translateY(-100%);
}

.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
  text-decoration: none;
  flex-shrink: 0;
}

.logo-img {
  height: 38px;
  width: auto;
  transition: height 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.header-scrolled .logo-img {
  height: 32px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  padding-left: 1rem;
}

.brand-name {
  font-size: 1.125rem;
  font-weight: 900;
  color: white;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.brand-tag {
  font-size: 0.7rem;
  font-weight: 600;
  color: hsla(0, 0%, 100%, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.nav-link {
  font-size: 0.9rem;
  font-weight: 600;
  color: hsla(0, 0%, 100%, 0.7);
  text-decoration: none;
  transition: all 0.2s;
}

.nav-link:hover, .router-link-active.nav-link {
  color: hsl(var(--gold));
}

.header-cta {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: hsl(var(--primary));
  font-size: 0.875rem;
  font-weight: 700;
  padding: 0.625rem 1.25rem;
  transition: transform 0.2s;
  border-radius: var(--radius);
}

.header-cta:hover {
  transform: translateY(-1px);
}

/* ── Footer ──────────────────────────────────────────────────────────────── */
.app-footer {
  color: white;
  padding: 5rem var(--spacing-container) 2rem var(--spacing-container);
  margin-top: auto;
}

.footer-inner {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1.5fr;
  gap: 4rem;
  margin-bottom: 4rem;
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.footer-logo-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.footer-logo {
  height: 36px;
  filter: brightness(0) invert(1);
}

.footer-brand-name {
  font-size: 1.5rem;
  font-weight: 900;
  color: hsl(var(--gold));
  letter-spacing: -0.02em;
}

.footer-tagline {
  font-size: 0.95rem;
  line-height: 1.6;
  opacity: 0.7;
  max-width: 320px;
}

.footer-socials {
  display: flex;
  gap: 1rem;
}

.social-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-radius: var(--radius);
  transition: all 0.2s;
}

.social-btn:hover {
  background: hsl(var(--gold));
  color: hsl(var(--primary));
  transform: translateY(-3px);
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.footer-heading {
  font-size: 0.875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: hsl(var(--gold));
}

.footer-links {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.footer-links a {
  font-size: 0.9rem;
  opacity: 0.7;
  transition: opacity 0.2s, color 0.2s;
}

.footer-links a:hover {
  opacity: 1;
  color: hsl(var(--gold));
}

.footer-contact {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.footer-contact li {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  opacity: 0.7;
  line-height: 1.5;
}

.footer-contact li .iconify {
  flex-shrink: 0;
  color: hsl(var(--gold));
  margin-top: 0.25rem;
}

.footer-bottom {
  max-width: 1280px;
  margin: 0 auto;
  padding-top: 2.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.footer-bottom p {
  font-size: 0.85rem;
  opacity: 0.6;
}

@media (max-width: 1024px) {
  .footer-inner {
    grid-template-columns: 1fr 1fr;
    gap: 3rem;
  }
}

@media (max-width: 640px) {
  .footer-inner {
    grid-template-columns: 1fr;
    gap: 2.5rem;
  }
  .header-nav { display: none; }
}
</style>
