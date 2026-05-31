<script setup>
const destinations = [
  { name: 'Siem Reap', img: '/img/temple.jpg', description: 'Home to the magnificent Angkor Wat and ancient Khmer history.' },
  { name: 'Phnom Penh', img: '/img/historical-site.jpg', description: 'The vibrant capital city blending modern growth with colonial charm.' },
  { name: 'Sihanoukville', img: '/img/beach.jpg', description: 'Pristine beaches and tropical islands on the Gulf of Thailand.' },
  { name: 'Kampot', img: '/img/water-fall.jpg', description: 'Relaxed riverside town famous for pepper and colonial architecture.' },
  { name: 'Battambang', img: '/img/art-gallary.jpg', description: 'The artistic heart of Cambodia with preserved French buildings.' },
  { name: 'Mondulkiri', img: '/img/wildlife-zoo.jpg', description: 'Rolling hills and ethnic minority cultures in the highlands.' }
]
</script>

<template>
  <div class="destinations-page">
    <section class="hero-section bg-royal-gradient">
      <div class="container">
        <h1 class="page-title">Destinations</h1>
        <p class="hero-subtitle">Explore the Wonders of Cambodia</p>
      </div>
    </section>

    <section class="grid-section">
      <div class="container">
        <div class="destinations-grid">
          <div v-for="dest in destinations" :key="dest.name" class="dest-card nextgen-card group">
            <div class="dest-image-wrapper">
              <img :src="dest.img" :alt="dest.name" class="dest-image" />
              <div class="dest-overlay">
                <button class="explore-btn bg-gold-gradient">Plan Trip</button>
              </div>
            </div>
            <div class="dest-info">
              <h3 class="dest-name">{{ dest.name }}</h3>
              <p class="dest-desc">{{ dest.description }}</p>
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

.grid-section {
  padding: 5rem 0;
}

.destinations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 2rem;
}

.dest-card {
  padding: 0;
  overflow: hidden;
  transition: transform 0.3s ease;
}

.dest-card:hover {
  transform: translateY(-5px);
}

.dest-image-wrapper {
  position: relative;
  height: 240px;
  overflow: hidden;
}

.dest-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.dest-card:hover .dest-image {
  transform: scale(1.1);
}

.dest-overlay {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(16, 32, 80, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.dest-card:hover .dest-overlay {
  opacity: 1;
}

.explore-btn {
  padding: 0.75rem 2rem;
  font-weight: 700;
  color: hsl(var(--primary));
  transform: translateY(20px);
  transition: transform 0.3s ease;
}

.dest-card:hover .explore-btn {
  transform: translateY(0);
}

.dest-info {
  padding: 1.5rem;
}

.dest-name {
  font-size: 1.5rem;
  color: hsl(var(--primary));
  margin-bottom: 0.75rem;
}

.dest-desc {
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

@media (max-width: 640px) {
  .destinations-grid { grid-template-columns: 1fr; }
}
</style>
