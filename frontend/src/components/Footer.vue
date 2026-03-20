<template>
    <footer class="bg-gradient-to-r from-teal-600 via-teal-500 to-sky-500 dark:from-slate-800 dark:via-slate-800 dark:to-slate-800 border-t border-teal-400/20 dark:border-slate-700">
        <div class="max-w-7xl mx-auto px-6 py-4">
            <div class="flex flex-col sm:flex-row items-center justify-between gap-4">

                <!-- Izquierda: Logo + nombre -->
                <div class="flex items-center gap-3">
                    <div class="w-9 h-9 bg-white/90 rounded-lg flex items-center justify-center p-1 flex-shrink-0">
                        <img :src="logoDre" alt="Logo DRE" class="w-full h-full object-contain" />
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="text-white font-bold text-sm">LectoSistem</span>
                            <span class="text-[10px] bg-amber-400 text-amber-900 px-2 py-0.5 rounded-full font-bold">DRE</span>
                        </div>
                        <p class="text-teal-100 dark:text-slate-400 text-[10px]">Dirección Regional de Educación · Huánuco</p>
                    </div>
                </div>

                <!-- Derecha: créditos + AI -->
                <div class="flex items-center gap-3 text-[10px] sm:text-xs text-white/70">
                    <span class="flex items-center gap-1">
                        <Heart class="w-3 h-3 text-red-400 fill-red-400" />
                        Hecho para la educación · © 2026
                    </span>
                    <span class="w-px h-4 bg-white/20"></span>
                    <div class="flex items-center gap-1.5 bg-white/10 px-2.5 py-1 rounded-full">
                        <img src="/icons/gemini.svg" alt="Gemini" class="w-3.5 h-3.5 object-contain" />
                        <span class="text-white/90 font-medium">Gemini Flash</span>
                    </div>
                </div>

            </div>
        </div>
    </footer>
</template>

<script setup>
import { Heart } from 'lucide-vue-next';
import logoDre from '../assets/logo.png';
</script>