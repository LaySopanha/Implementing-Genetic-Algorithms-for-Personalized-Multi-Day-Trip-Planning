import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AboutView from '../views/AboutView.vue'
import HowItWorksView from '../views/HowItWorksView.vue'
import DestinationsView from '../views/DestinationsView.vue'
import ItineraryView from '../views/ItineraryView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/itinerary',
    name: 'itinerary',
    component: ItineraryView
  },
  {
    path: '/about',
    name: 'about',
    component: AboutView
  },
  {
    path: '/how-it-works',
    name: 'how-it-works',
    component: HowItWorksView
  },
  {
    path: '/destinations',
    name: 'destinations',
    component: DestinationsView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

export default router
