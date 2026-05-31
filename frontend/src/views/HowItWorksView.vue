<script setup>
import { Icon } from '@iconify/vue'
</script>

<template>
  <div class="how-it-works">
    <section class="hero-section bg-royal-gradient">
      <div class="container">
        <h1 class="page-title">How It Works</h1>
        <p class="hero-subtitle">Sophisticated Algorithms, Simple Experience</p>
      </div>
    </section>

    <section class="steps-section">
      <div class="container">
        <div class="steps-grid">
          <div class="step-card nextgen-card">
            <div class="step-icon bg-gold-gradient">
              <Icon icon="lucide:map-pin" width="32" height="32" />
            </div>
            <h3 class="step-title">1. Define Preferences</h3>
            <p>Select your destination, trip duration, and preferred activities. Choose a planning mode: Adventure, Balanced, or Chill.</p>
          </div>

          <div class="step-card nextgen-card">
            <div class="step-icon bg-gold-gradient">
              <Icon icon="lucide:cpu" width="32" height="32" />
            </div>
            <h3 class="step-title">2. AI Optimization</h3>
            <p>Our hybrid Memetic Algorithm analyzes thousands of data points to cluster activities geographically and optimize your route.</p>
          </div>

          <div class="step-card nextgen-card">
            <div class="step-icon bg-gold-gradient">
              <Icon icon="lucide:calendar-check" width="32" height="32" />
            </div>
            <h3 class="step-title">3. Get Your Itinerary</h3>
            <p>Receive a complete multi-day plan with optimized travel times, daily schedules, and recommended dining and stay options.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="tech-section bg-muted">
      <div class="container">
        <div class="tech-content">
          <h2 class="section-heading">The Technology Behind Sak Tmor</h2>
          <div class="tech-grid">
            <div class="tech-item">
              <h4 class="tech-label">Recommendation</h4>
              <p>TF-IDF content-based filtering combined with weighted scoring for authentic "hidden gems."</p>
            </div>
            <div class="tech-item">
              <h4 class="tech-label">Clustering</h4>
              <p>K-Means spatial clustering ensures geographic coherence across multi-day trips.</p>
            </div>
            <div class="tech-item">
              <h4 class="tech-label">Optimization</h4>
              <p>Hybrid Genetic Algorithm + 2-opt local search minimizes total travel distance.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--spacing-container);
}

.hero-section {
  color: white;
  padding: 6rem 0;
  text-align: center;
}

.page-title {
  font-size: 3.5rem;
  font-weight: 900;
  margin-bottom: 1rem;
}

.hero-subtitle {
  font-size: 1.25rem;
  opacity: 0.8;
}

.steps-section {
  padding: 5rem 0;
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
}

.step-card {
  padding: 3rem 2rem;
  text-align: center;
}

.step-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: hsl(var(--primary));
  border-radius: var(--radius);
}

.step-title {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: hsl(var(--primary));
}

.tech-section {
  padding: 5rem 0;
}

.section-heading {
  font-size: 2.25rem;
  text-align: center;
  margin-bottom: 3rem;
  color: hsl(var(--primary));
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3rem;
}

.tech-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: hsl(var(--gold));
  margin-bottom: 0.5rem;
  letter-spacing: 0.1em;
}

@media (max-width: 900px) {
  .steps-grid, .tech-grid { grid-template-columns: 1fr; }
}
</style>
