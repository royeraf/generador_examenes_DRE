<script setup lang="ts">
import { Sun, Moon, Monitor } from 'lucide-vue-next'
import { useTheme, type ThemeMode } from '../composables/useTheme'

const { themeMode, setMode } = useTheme()

const options: { value: ThemeMode; icon: typeof Sun; label: string }[] = [
  { value: 'light',  icon: Sun,     label: 'Claro'    },
  { value: 'system', icon: Monitor, label: 'Sistema'  },
  { value: 'dark',   icon: Moon,    label: 'Oscuro'   },
]
</script>

<template>
  <div
    class="inline-flex items-center bg-white/80 dark:bg-slate-800/80 backdrop-blur-md rounded-full p-1 shadow-lg border border-slate-200/60 dark:border-slate-700/60 gap-0.5"
    role="group"
    aria-label="Tema de color"
  >
    <button
      v-for="opt in options"
      :key="opt.value"
      @click="setMode(opt.value)"
      :title="opt.label"
      :aria-pressed="themeMode === opt.value"
      class="relative flex items-center justify-center w-8 h-8 rounded-full transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-500"
      :class="themeMode === opt.value
        ? 'bg-gradient-to-br from-teal-500 to-indigo-600 text-white shadow-md'
        : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700'"
    >
      <component :is="opt.icon" class="w-4 h-4" />
    </button>
  </div>
</template>
