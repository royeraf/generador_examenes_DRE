<template>
    <footer class="relative z-10 bg-surface border-t border-slate-200 dark:border-slate-800">
        <div class="max-w-7xl mx-auto px-6 py-4">
            <div class="flex flex-col sm:flex-row items-center justify-between gap-4">

                <!-- Izquierda: Logo + nombre -->
                <div class="flex items-center gap-3">
                    <div class="w-9 h-9 bg-slate-100 dark:bg-surface-card rounded-lg flex items-center justify-center p-1 flex-shrink-0">
                        <img :src="logoDre" alt="Logo DRE" class="w-full h-full object-contain" />
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="text-text font-bold text-sm">SIEVA</span>
                            <span class="text-[10px] bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-2 py-0.5 rounded-full font-bold">DRE</span>
                        </div>
                        <p class="text-slate-400 dark:text-text-subtle text-[10px]">Dirección Regional de Educación · Huánuco</p>
                    </div>
                </div>

                <!-- Derecha: créditos + AI -->
                <div class="flex items-center gap-3 text-[10px] sm:text-xs text-slate-400 dark:text-text-subtle">
                    <span class="flex items-center gap-1">
                        <Heart class="w-3 h-3 text-red-400 fill-red-400" />
                        Hecho para la educación · © 2026
                    </span>
                    <span class="w-px h-4 bg-slate-200 dark:bg-surface-input"></span>
                    <div class="flex items-center gap-1.5 bg-slate-100 dark:bg-surface-card px-2.5 py-1 rounded-full">
                        <img src="/icons/gemini.svg" alt="Gemini" class="w-3.5 h-3.5 object-contain" />
                        <span class="text-slate-600 dark:text-text-muted font-medium">Gemini Flash</span>
                    </div>
                </div>

            </div>
        </div>
    </footer>
</template>

<script setup>
import { Heart } from 'lucide-vue-next';
import logoDre from '../../assets/logo.png';
</script>