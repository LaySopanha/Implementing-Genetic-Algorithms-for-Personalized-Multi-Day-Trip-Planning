<template>
  <div class="about-page">
    <section class="hero-section bg-royal-gradient">
      <div class="container">
        <h1 class="page-title">About Sak Tmor</h1>
        <p class="hero-subtitle">The Future of AI-Powered Travel in Cambodia</p>
      </div>
    </section>

    <section class="content-section">
      <div class="container">
        <div class="grid">
          <div class="text-content">
            <h2 class="section-heading">Our Mission</h2>
            <p>Sak Tmor (សាក់ថ្ម) is a research-quality trip planning system designed to generate personalized, geographically coherent, and efficient multi-day itineraries for Cambodia. Our mission is to bridge the gap between content-based recommendation and route optimization.</p>
            
            <h2 class="section-heading mt-8">NextGen Innovation</h2>
            <p>Developed at NextGen, Sak Tmor leverages state-of-the-art machine learning and genetic algorithms to solve the complex problem of multi-day trip planning. We prioritize data quality, smart recommendations, and route efficiency to provide a seamless user experience.</p>
          </div>
          <div class="stats-grid">
            <div class="nextgen-card stat-card">
              <span class="stat-value">6K+</span>
              <span class="stat-label">Verified Places</span>
            </div>
            <div class="nextgen-card stat-card">
              <span class="stat-value">25+</span>
              <span class="stat-label">Provinces Covered</span>
            </div>
            <div class="nextgen-card stat-card">
              <span class="stat-value">< 1s</span>
              <span class="stat-label">Itinerary Generation</span>
            </div>
            <div class="nextgen-card stat-card border-gold">
              <span class="stat-value">AI</span>
              <span class="stat-label">Driven Optimization</span>
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

.content-section {
  padding: 5rem 0;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
}

.section-heading {
  font-size: 2rem;
  color: hsl(var(--primary));
  margin-bottom: 1.5rem;
}

.mt-8 { margin-top: 2rem; }

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem;
  text-align: center;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: hsl(var(--primary));
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-secondary);
}

.border-gold {
  border-color: hsl(var(--gold));
}

@media (max-width: 768px) {
  .grid { grid-template-columns: 1fr; }
  .page-title { font-size: 2.5rem; }
}
</style>
