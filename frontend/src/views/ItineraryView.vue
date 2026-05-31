<script setup>
import { ref, onMounted, inject, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import ResultView from '../components/ResultView.vue'

const route = useRoute()
const router = useRouter()
const setResultMode = inject('setResultMode')

const loading = ref(true)
const apiError = ref('')
const itineraryResult = ref(null)

const fetchItinerary = async (params) => {
  loading.value = true
  apiError.value = ''

  const startTime = Date.now()
  const MIN_DELAY = 2500

  try {
    const response = await axios.post('/api/generate-trip', params, { timeout: 30000 })
    
    const elapsed = Date.now() - startTime
    if (elapsed < MIN_DELAY) {
      await new Promise(resolve => setTimeout(resolve, MIN_DELAY - elapsed))
    }
    
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

const handleRestart = () => {
  router.push('/')
}

onMounted(() => {
  if (setResultMode) setResultMode(true)
  
  // Extract params from query
  const query = route.query
  if (!query.province) {
    router.push('/')
    return
  }

  const params = {
    province: query.province,
    days: parseInt(query.days) || 3,
    perDay: parseInt(query.perDay) || 3,
    activities: query.activities ? (Array.isArray(query.activities) ? query.activities : [query.activities]) : [],
    accommodation: query.accommodation ? (Array.isArray(query.accommodation) ? query.accommodation : [query.accommodation]) : [],
    dining: query.dining ? (Array.isArray(query.dining) ? query.dining : [query.dining]) : []
  }

  fetchItinerary(params)
})

onUnmounted(() => {
  if (setResultMode) setResultMode(false)
})
</script>

<template>
  <div class="itinerary-page">
    <ResultView 
      :loading="loading" 
      :result="itineraryResult" 
      :error="apiError" 
      @restart="handleRestart" 
    />
  </div>
</template>

<style scoped>
.itinerary-page {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
