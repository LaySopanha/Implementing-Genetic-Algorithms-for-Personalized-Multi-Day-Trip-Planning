import { createApp } from 'vue'
import axios from 'axios'
import App from './App.vue'
import router from './router'
import './index.css'

// In prod, VITE_API_URL points at the deployed backend (e.g. HF Space).
// Empty in dev → relative /api, handled by the vite proxy.
axios.defaults.baseURL = import.meta.env.VITE_API_URL || ''

const app = createApp(App)
app.use(router)
app.mount('#app')
