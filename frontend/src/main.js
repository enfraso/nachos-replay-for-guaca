/**
 * Nachos Replay - Main Entry Point
 */
import { createApp } from 'vue'
import { pinia } from './stores'
import router from './router'
import i18n from './i18n'
import App from './App.vue'

import './assets/styles/main.css'

const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(i18n)

app.mount('#app')
