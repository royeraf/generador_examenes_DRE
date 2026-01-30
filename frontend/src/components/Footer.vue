<template>
    <footer
        class="bg-gradient-to-r from-teal-600 via-teal-500 to-sky-500 dark:from-slate-800 dark:via-slate-800 dark:to-slate-800 border-t border-teal-400/20 dark:border-slate-700 py-6">
        <div class="max-w-7xl mx-auto px-6">
            <div class="flex flex-col lg:flex-row items-center justify-between gap-6">
                <!-- Logo y Nombre -->
                <div class="flex items-center gap-3 w-full lg:w-auto justify-center lg:justify-start">
                    <div
                        class="w-10 h-10 sm:w-12 sm:h-12 bg-white/90 backdrop-blur-sm rounded-xl flex items-center justify-center p-1 flex-shrink-0">
                        <img :src="logoDre" alt="Logo DRE" class="w-full h-full object-contain" />
                    </div>
                    <div>
                        <h3 class="text-white font-bold text-sm sm:text-base flex items-center gap-2">
                            LectoSistem
                            <span
                                class="text-[10px] sm:text-xs bg-amber-400 text-amber-900 px-2 py-0.5 rounded-full">DRE</span>
                        </h3>
                        <p class="text-teal-100 dark:text-slate-400 text-[10px] sm:text-xs">La aventura de una lectura
                            inteligente</p>
                    </div>
                </div>

                <!-- Información Central -->
                <div class="flex items-center gap-2 text-white/90 text-xs sm:text-sm text-center lg:text-left">
                    <GraduationCap class="w-4 h-4 sm:w-5 sm:h-5 text-amber-300 flex-shrink-0" />
                    <p class="font-medium">
                        Dirección Regional de Educación - <span
                            class="text-amber-300 font-bold block sm:inline">Huánuco</span>
                    </p>
                </div>

                <!-- Año y Créditos -->
                <div
                    class="flex flex-wrap items-center justify-center gap-2 sm:gap-3 text-white/80 text-[10px] sm:text-xs">
                    <div class="flex items-center gap-1.5 bg-white/10 backdrop-blur-sm px-3 py-1.5 rounded-full">
                        <Star class="w-3 h-3 sm:w-4 sm:h-4 text-amber-300" />
                        <span>© 2026</span>
                    </div>
                    <div class="flex items-center gap-1.5 bg-white/10 backdrop-blur-sm px-3 py-1.5 rounded-full">
                        <Sparkles class="w-3 h-3 sm:w-4 sm:h-4 text-sky-300" />
                        <span>Hecho con
                            <Heart class="w-3 h-3 sm:w-4 sm:h-4 inline text-red-400 fill-red-400" /> para la educación
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </footer>
</template>

<script setup>
import { Sparkles, GraduationCap, Star, Heart } from 'lucide-vue-next';
import logoDre from '../assets/logo.png';
</script>