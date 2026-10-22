<template>
    <footer
        class="footer-edu z-20 shrink-0 border-t border-teal-200/70 dark:border-slate-800 transition-colors duration-300"
        :class="fixed ? 'fixed inset-x-0 bottom-0' : 'sticky bottom-0 mt-auto'">
        <div
            class="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-start gap-2 sm:gap-3 overflow-hidden">
            <p class="text-[10px] sm:text-[11px] leading-tight whitespace-nowrap truncate">
                <span class="footer-brand font-bold text-slate-800 dark:text-slate-100 tracking-wide">SIEVA</span>
                <span class="text-amber-500/80 dark:text-amber-400/80 mx-1">·</span>
                <span class="text-slate-500 dark:text-slate-400">Sistema Integrado de Evaluación en Aula</span>
            </p>
            <span class="w-px h-3.5 bg-teal-300/60 dark:bg-slate-700 shrink-0"></span>
            <p class="flex items-center gap-1 text-[10px] sm:text-[11px] text-slate-400 dark:text-slate-500 whitespace-nowrap shrink-0">
                <Copyright class="w-3 h-3" />
                <span>{{ currentYear }}</span>
            </p>
        </div>
    </footer>
</template>

<script setup lang="ts">
import { Copyright } from 'lucide-vue-next'

withDefaults(defineProps<{ fixed?: boolean }>(), { fixed: false })

const currentYear = new Date().getFullYear()
</script>

<style scoped>
/* ── Footer educativo: papel de cuaderno + acento de logro ── */
.footer-edu {
    position: relative;
    background-color: #ffffff;
    background-image:
        radial-gradient(ellipse at 8% 0%, rgba(20, 184, 166, 0.10), transparent 55%),
        radial-gradient(ellipse at 92% 100%, rgba(245, 158, 11, 0.08), transparent 55%),
        radial-gradient(rgba(13, 148, 136, 0.10) 1px, transparent 1px);
    background-size: auto, auto, 16px 16px;
}

.dark .footer-edu {
    background-color: #0f172a;
    background-image:
        radial-gradient(ellipse at 8% 0%, rgba(20, 184, 166, 0.12), transparent 55%),
        radial-gradient(ellipse at 92% 100%, rgba(245, 158, 11, 0.10), transparent 55%),
        radial-gradient(rgba(94, 234, 212, 0.10) 1px, transparent 1px);
}

/* Wordmark en Fredoka, la fuente de titulares del sistema */
.footer-brand {
    font-family: var(--font-heading);
}
</style>
