import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router'],
          d3: ['d3'],
          xlsx: ['xlsx'],
          ui: ['lucide-vue-next', 'sweetalert2'],
          forms: ['vee-validate', '@vee-validate/rules', 'yup'],
        },
      },
    },
  },
})
