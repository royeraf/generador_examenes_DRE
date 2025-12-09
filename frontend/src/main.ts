import { createApp } from 'vue'
import './style.css'
import App from './App.vue'

// Import theme composable to apply dark mode class immediately
import './composables/useTheme'

createApp(App).mount('#app')
