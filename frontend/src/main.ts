import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import 'katex/dist/katex.min.css'
import App from './App.vue'
import router from './router'

// Import theme composable to apply dark mode class immediately
import './shared/composables/useTheme'

// Bloquea pinch-zoom y doble toque en móviles/tablets (iOS Safari lo ignora vía meta)
import { usePreventZoom } from './shared/composables/usePreventZoom'

usePreventZoom()

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
