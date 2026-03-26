<script setup lang="ts">
import { BookOpen, Calculator, Sparkles, GraduationCap, Users, ArrowRight, Settings, BarChart3 } from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import UserBadge from '../components/UserBadge.vue';
import logoDre from '../assets/logo.png';

const router = useRouter();
const auth = useAuthStore();
</script>

<template>
    <div
        class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 to-gray-100 dark:from-slate-900 dark:to-slate-950 relative overflow-hidden transition-colors duration-500">

        <!-- Background blobs -->
        <div class="absolute inset-0 overflow-hidden pointer-events-none">
            <div
                class="absolute top-[-12%] left-[-8%] w-[30rem] h-[30rem] bg-teal-200/25 dark:bg-teal-500/8 rounded-full blur-3xl animate-blob-1 will-change-transform">
            </div>
            <div
                class="absolute bottom-[-12%] right-[-8%] w-[34rem] h-[34rem] bg-indigo-200/25 dark:bg-indigo-500/8 rounded-full blur-3xl animate-blob-2 will-change-transform">
            </div>
            <div
                class="absolute top-[35%] right-[8%] w-72 h-72 bg-amber-200/15 dark:bg-amber-500/6 rounded-full blur-3xl animate-blob-3 will-change-transform">
            </div>
            <div
                class="absolute bottom-[8%] left-[8%] w-80 h-80 bg-rose-200/10 dark:bg-rose-500/5 rounded-full blur-3xl animate-blob-4 will-change-transform">
            </div>
        </div>

        <!-- Top bar -->
        <div
            class="fixed top-0 left-0 right-0 z-[100] flex items-center justify-between px-4 py-3 sm:px-6 sm:py-4 pointer-events-none">
            <div class="pointer-events-auto">
                <div class="relative w-10 h-10 sm:w-12 sm:h-12">
                    <div
                        class="absolute -inset-0.5 bg-gradient-to-r from-teal-500 to-indigo-600 rounded-xl blur opacity-30 animate-logo-glow">
                    </div>
                    <div
                        class="absolute inset-0 flex items-center justify-center p-2 bg-white/80 dark:bg-slate-800/80 backdrop-blur-md rounded-xl shadow-lg border border-slate-100 dark:border-slate-700 transition-transform hover:scale-105 overflow-hidden">
                        <GraduationCap
                            class="absolute w-5 h-5 sm:w-6 sm:h-6 text-teal-600 dark:text-teal-400 animate-logo-cycle-1" />
                        <div class="absolute logo-gradient-display-static w-5 h-5 sm:w-6 sm:h-6 animate-logo-cycle-2"
                            :style="{ 'mask-image': `url(${logoDre})`, '-webkit-mask-image': `url(${logoDre})` }"></div>
                    </div>
                </div>
            </div>
            <div class="flex items-center gap-2 pointer-events-auto">
                <UserBadge />
            </div>
        </div>

        <!-- Main content -->
        <div class="relative z-10 flex flex-col flex-1 justify-center px-4 pt-20 pb-8 sm:pt-24 sm:pb-10">
            <div class="max-w-3xl w-full mx-auto space-y-6 sm:space-y-8">

                <!-- Header -->
                <div class="text-center space-y-1 sm:space-y-2">
                    <p
                        class="text-sm sm:text-base font-semibold text-slate-500 dark:text-slate-400 animate-spring-down delay-0">
                        Bienvenido, <span class="text-teal-600 dark:text-teal-400 font-bold">{{
                            auth.user?.nombres?.split(' ')[0] ?? auth.user?.dni }}</span>
                    </p>
                    <h1
                        class="text-2xl sm:text-3xl md:text-4xl font-black text-slate-800 dark:text-white tracking-tight leading-tight animate-spring-down delay-150">
                        Sistema Integrado de<br />
                        <span class="shimmer-text">Evaluación de Aula (SIEVA)</span>
                    </h1>
                    <p class="text-sm sm:text-base text-slate-500 dark:text-slate-400 pt-1 animate-fade-blur delay-300">
                        Selecciona el módulo para comenzar a generar evaluaciones con IA
                    </p>
                </div>

                <!-- Module cards -->
                <div class="grid sm:grid-cols-2 gap-3 sm:gap-4">

                    <!-- LectoSistem -->
                    <button @click="router.push('/lectosistem')" class="module-card-teal group relative bg-white dark:bg-slate-800 rounded-2xl p-5 sm:p-6 text-left overflow-hidden flex flex-col gap-4 animate-slide-left delay-450
                               border border-slate-100 dark:border-slate-700 hover:border-teal-200 dark:hover:border-teal-700/60
                               shadow-lg shadow-slate-900/8 dark:shadow-black/30 hover:shadow-xl hover:shadow-teal-500/15 dark:hover:shadow-teal-500/10">

                        <!-- Hover tint overlay -->
                        <div class="card-overlay absolute inset-0 rounded-2xl pointer-events-none z-0"></div>

                        <!-- Bottom accent line -->
                        <div
                            class="card-line absolute bottom-0 left-8 right-8 h-[2px] rounded-full pointer-events-none z-0">
                        </div>

                        <!-- Watermark -->
                        <div
                            class="absolute -right-4 -bottom-4 pointer-events-none z-0 opacity-[0.04] group-hover:opacity-[0.09] transition-opacity duration-150">
                            <BookOpen class="w-32 h-32 text-teal-500" />
                        </div>

                        <div class="flex items-start justify-between gap-3 relative z-10">
                            <div
                                class="card-icon-teal w-11 h-11 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center shrink-0">
                                <BookOpen class="w-5 h-5 text-white" />
                            </div>
                            <span
                                class="text-[10px] font-bold text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-900/30 px-2 py-0.5 rounded-full uppercase tracking-wide border border-teal-100 dark:border-teal-800/50">
                                Comunicación
                            </span>
                        </div>

                        <div class="relative z-10 flex-1">
                            <h2
                                class="text-lg sm:text-xl font-bold text-slate-800 dark:text-white mb-1 group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors duration-150">
                                LectoSistem
                            </h2>
                            <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                                Genera exámenes de comprensión lectora con niveles literal, inferencial y crítico.
                            </p>
                        </div>

                        <div class="relative z-10">
                            <span class="text-xs font-bold text-teal-600 dark:text-teal-400 flex items-center gap-2">
                                Ingresar al módulo
                                <ArrowRight
                                    class="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform duration-150" />
                            </span>
                        </div>
                    </button>

                    <!-- MatSistem -->
                    <button @click="router.push('/matsistem')" class="module-card-indigo group relative bg-white dark:bg-slate-800 rounded-2xl p-5 sm:p-6 text-left overflow-hidden flex flex-col gap-4 animate-slide-right delay-550
                               border border-slate-100 dark:border-slate-700 hover:border-indigo-200 dark:hover:border-indigo-700/60
                               shadow-lg shadow-slate-900/8 dark:shadow-black/30 hover:shadow-xl hover:shadow-indigo-500/15 dark:hover:shadow-indigo-500/10">

                        <!-- Hover tint overlay -->
                        <div class="card-overlay absolute inset-0 rounded-2xl pointer-events-none z-0"></div>

                        <!-- Bottom accent line -->
                        <div
                            class="card-line absolute bottom-0 left-8 right-8 h-[2px] rounded-full pointer-events-none z-0">
                        </div>

                        <!-- Watermark -->
                        <div
                            class="absolute -right-4 -bottom-4 pointer-events-none z-0 opacity-[0.04] group-hover:opacity-[0.09] transition-opacity duration-150">
                            <Calculator class="w-32 h-32 text-indigo-500" />
                        </div>

                        <div class="flex items-start justify-between gap-3 relative z-10">
                            <div
                                class="card-icon-indigo w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center shrink-0">
                                <Calculator class="w-5 h-5 text-white" />
                            </div>
                            <span
                                class="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded-full uppercase tracking-wide border border-indigo-100 dark:border-indigo-800/50">
                                Matemática
                            </span>
                        </div>

                        <div class="relative z-10 flex-1">
                            <h2
                                class="text-lg sm:text-xl font-bold text-slate-800 dark:text-white mb-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors duration-150">
                                MatSistem
                            </h2>
                            <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                                Genera prácticas matemáticas por competencia, capacidad y grado escolar.
                            </p>
                        </div>

                        <div class="relative z-10">
                            <span
                                class="text-xs font-bold text-indigo-600 dark:text-indigo-400 flex items-center gap-2">
                                Ingresar al módulo
                                <ArrowRight
                                    class="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform duration-150" />
                            </span>
                        </div>
                    </button>

                </div>

                <!-- Admin panel -->
                <div v-if="auth.isAdmin">

                    <div class="flex items-center gap-3 mb-3 animate-fade-blur delay-650">
                        <div class="h-px flex-1 bg-slate-200 dark:bg-slate-700/80"></div>
                        <span
                            class="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">
                            <Settings class="w-3 h-3" /> Administración
                        </span>
                        <div class="h-px flex-1 bg-slate-200 dark:bg-slate-700/80"></div>
                    </div>

                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3">

                        <button @click="router.push('/admin')"
                            class="admin-card group flex flex-col items-center gap-2 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/80 rounded-xl p-3 sm:p-4 hover:shadow-md hover:shadow-teal-500/15 hover:border-teal-300/70 dark:hover:border-teal-600/70 animate-scale-in delay-700">
                            <div
                                class="admin-icon w-8 h-8 rounded-lg bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center shadow-sm">
                                <BookOpen class="w-4 h-4 text-white" />
                            </div>
                            <div class="text-center">
                                <p class="text-[11px] font-bold text-slate-700 dark:text-slate-200 leading-tight">
                                    Comunicación</p>
                                <p class="text-[9px] text-slate-400 dark:text-slate-500 leading-tight">Desempeños</p>
                            </div>
                        </button>

                        <button @click="router.push('/admin/mat')"
                            class="admin-card group flex flex-col items-center gap-2 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/80 rounded-xl p-3 sm:p-4 hover:shadow-md hover:shadow-indigo-500/15 hover:border-indigo-300/70 dark:hover:border-indigo-600/70 animate-scale-in delay-800">
                            <div
                                class="admin-icon w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center shadow-sm">
                                <Calculator class="w-4 h-4 text-white" />
                            </div>
                            <div class="text-center">
                                <p class="text-[11px] font-bold text-slate-700 dark:text-slate-200 leading-tight">
                                    Matemática</p>
                                <p class="text-[9px] text-slate-400 dark:text-slate-500 leading-tight">Desempeños</p>
                            </div>
                        </button>

                        <button @click="router.push('/admin/usuarios')"
                            class="admin-card group flex flex-col items-center gap-2 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/80 rounded-xl p-3 sm:p-4 hover:shadow-md hover:shadow-violet-500/15 hover:border-violet-300/70 dark:hover:border-violet-600/70 animate-scale-in delay-900">
                            <div
                                class="admin-icon w-8 h-8 rounded-lg bg-gradient-to-br from-violet-400 to-pink-500 flex items-center justify-center shadow-sm">
                                <Users class="w-4 h-4 text-white" />
                            </div>
                            <div class="text-center">
                                <p class="text-[11px] font-bold text-slate-700 dark:text-slate-200 leading-tight">
                                    Usuarios</p>
                                <p class="text-[9px] text-slate-400 dark:text-slate-500 leading-tight">Gestión</p>
                            </div>
                        </button>

                        <button @click="router.push('/admin/metricas')"
                            class="admin-card group flex flex-col items-center gap-2 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/80 rounded-xl p-3 sm:p-4 hover:shadow-md hover:shadow-indigo-500/15 hover:border-indigo-300/70 dark:hover:border-indigo-600/70 animate-scale-in delay-950">
                            <div
                                class="admin-icon w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-sm">
                                <BarChart3 class="w-4 h-4 text-white" />
                            </div>
                            <div class="text-center">
                                <p class="text-[11px] font-bold text-slate-700 dark:text-slate-200 leading-tight">
                                    Métricas</p>
                                <p class="text-[9px] text-slate-400 dark:text-slate-500 leading-tight">Uso del sistema</p>
                            </div>
                        </button>

                    </div>
                </div>

                <!-- Footer -->
                <p :class="auth.isAdmin ? 'delay-950' : 'delay-650'"
                    class="text-center text-[11px] text-slate-400 dark:text-slate-600 flex items-center justify-center gap-1.5 animate-fade-blur">
                    <Sparkles class="w-3 h-3 animate-sparkle" /> Desarrollado para la Dirección Regional de Educación
                    Huánuco
                </p>

            </div>
        </div>
    </div>
</template>

<style scoped>
/* ── Background blobs ─────────────────────────────── */
.animate-blob-1 {
    animation: blob1 9s ease-in-out infinite;
}

.animate-blob-2 {
    animation: blob2 13s ease-in-out infinite;
}

.animate-blob-3 {
    animation: blob3 7s ease-in-out infinite;
}

.animate-blob-4 {
    animation: blob4 16s ease-in-out infinite;
}

@keyframes blob1 {

    0%,
    100% {
        transform: translate(0, 0) scale(1);
    }

    25% {
        transform: translate(45px, -65px) scale(1.12);
    }

    50% {
        transform: translate(-28px, 35px) scale(0.92);
    }

    75% {
        transform: translate(55px, 18px) scale(1.06);
    }
}

@keyframes blob2 {

    0%,
    100% {
        transform: translate(0, 0) scale(1);
    }

    20% {
        transform: translate(-55px, 48px) scale(1.08);
    }

    55% {
        transform: translate(38px, -52px) scale(0.87);
    }

    80% {
        transform: translate(-22px, -28px) scale(1.04);
    }
}

@keyframes blob3 {

    0%,
    100% {
        transform: translate(0, 0) scale(1);
    }

    33% {
        transform: translate(-32px, -48px) scale(1.18);
    }

    66% {
        transform: translate(28px, 32px) scale(0.86);
    }
}

@keyframes blob4 {

    0%,
    100% {
        transform: translate(0, 0) scale(1);
    }

    30% {
        transform: translate(62px, -38px) scale(0.9);
    }

    65% {
        transform: translate(-48px, 58px) scale(1.12);
    }
}

/* ── Entrance animations ──────────────────────────── */
.animate-spring-down {
    animation: springDown 0.65s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

.animate-slide-left {
    animation: slideLeft 0.6s cubic-bezier(0.34, 1.4, 0.64, 1) both;
}

.animate-slide-right {
    animation: slideRight 0.6s cubic-bezier(0.34, 1.4, 0.64, 1) both;
}

.animate-scale-in {
    animation: scaleIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

.animate-fade-blur {
    animation: fadeBlur 0.65s ease-out both;
}

@keyframes springDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideLeft {
    from {
        opacity: 0;
        transform: translateX(-30px) translateY(8px);
    }

    to {
        opacity: 1;
        transform: translateX(0) translateY(0);
    }
}

@keyframes slideRight {
    from {
        opacity: 0;
        transform: translateX(30px) translateY(8px);
    }

    to {
        opacity: 1;
        transform: translateX(0) translateY(0);
    }
}

@keyframes scaleIn {
    from {
        opacity: 0;
        transform: scale(0.8) translateY(12px);
    }

    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

@keyframes fadeBlur {
    from {
        opacity: 0;
        filter: blur(6px);
        transform: translateY(8px);
    }

    to {
        opacity: 1;
        filter: blur(0);
        transform: translateY(0);
    }
}

/* ── Delays ───────────────────────────────────────── */
.delay-0 {
    animation-delay: 0ms;
}

.delay-150 {
    animation-delay: 150ms;
}

.delay-300 {
    animation-delay: 300ms;
}

.delay-450 {
    animation-delay: 450ms;
}

.delay-550 {
    animation-delay: 550ms;
}

.delay-650 {
    animation-delay: 650ms;
}

.delay-700 {
    animation-delay: 700ms;
}

.delay-800 {
    animation-delay: 800ms;
}

.delay-900 {
    animation-delay: 900ms;
}

.delay-950 {
    animation-delay: 950ms;
}

/* ── Shimmer gradient title ───────────────────────── */
.shimmer-text {
    background: linear-gradient(90deg, #14b8a6, #6366f1, #0ea5e9, #8b5cf6, #14b8a6);
    background-size: 250% auto;
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: shimmerText 4s linear infinite;
    animation-delay: 1.2s;
}

.dark .shimmer-text {
    background: linear-gradient(90deg, #5eead4, #818cf8, #38bdf8, #a78bfa, #5eead4);
    background-size: 250% auto;
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    animation: shimmerText 4s linear infinite;
    animation-delay: 1.2s;
}

@keyframes shimmerText {
    0% {
        background-position: 0% center;
    }

    100% {
        background-position: 250% center;
    }
}

/* ── Card lift transitions (GPU-accelerated) ──────── */
.module-card-teal,
.module-card-indigo {
    will-change: transform;
    transition: transform 75ms ease-out;
}

.module-card-teal:hover {
    transform: translateY(-8px);
}

.module-card-indigo:hover {
    transform: translateY(-8px);
}

.admin-card {
    will-change: transform;
    transition: transform 75ms ease-out;
}

.admin-card:hover {
    transform: translateY(-4px);
}

.admin-card .admin-icon {
    transition: transform 75ms ease-out;
}

.admin-card:hover .admin-icon {
    transform: scale(1.1);
}

/* ── Module card hover effects ────────────────────── */
/* Radial gradient tint overlay */
.module-card-teal .card-overlay {
    background: radial-gradient(ellipse at 18% 25%, rgba(20, 184, 166, 0.09) 0%, transparent 62%);
    opacity: 0;
    transition: opacity 0.1s ease-out;
}

.module-card-teal:hover .card-overlay {
    opacity: 1;
}

.module-card-indigo .card-overlay {
    background: radial-gradient(ellipse at 18% 25%, rgba(99, 102, 241, 0.09) 0%, transparent 62%);
    opacity: 0;
    transition: opacity 0.1s ease-out;
}

.module-card-indigo:hover .card-overlay {
    opacity: 1;
}

/* Bottom accent line grows from center */
.module-card-teal .card-line {
    background: linear-gradient(90deg, transparent, rgba(20, 184, 166, 0.85), rgba(16, 185, 129, 0.85), transparent);
    transform: scaleX(0);
    transition: transform 0.15s cubic-bezier(0.34, 1.4, 0.64, 1);
    transform-origin: center;
}

.module-card-teal:hover .card-line {
    transform: scaleX(1);
}

.module-card-indigo .card-line {
    background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.85), rgba(168, 85, 247, 0.85), transparent);
    transform: scaleX(0);
    transition: transform 0.15s cubic-bezier(0.34, 1.4, 0.64, 1);
    transform-origin: center;
}

.module-card-indigo:hover .card-line {
    transform: scaleX(1);
}

/* Icon — base shadow + hover glow ring */
.card-icon-teal {
    box-shadow: 0 4px 8px -2px rgba(20, 184, 166, 0.3);
    transition: transform 0.1s ease-out, box-shadow 0.1s ease-out;
}

.module-card-teal:hover .card-icon-teal {
    transform: scale(1.06);
    box-shadow:
        0 0 0 3px rgba(20, 184, 166, 0.22),
        0 0 14px rgba(20, 184, 166, 0.38),
        0 4px 10px rgba(20, 184, 166, 0.25);
}

.card-icon-indigo {
    box-shadow: 0 4px 8px -2px rgba(99, 102, 241, 0.3);
    transition: transform 0.1s ease-out, box-shadow 0.1s ease-out;
}

.module-card-indigo:hover .card-icon-indigo {
    transform: scale(1.06);
    box-shadow:
        0 0 0 3px rgba(99, 102, 241, 0.22),
        0 0 14px rgba(99, 102, 241, 0.38),
        0 4px 10px rgba(99, 102, 241, 0.25);
}

/* ── Logo glow pulse ──────────────────────────────── */
.animate-logo-glow {
    animation: logoGlow 3s ease-in-out infinite;
}

@keyframes logoGlow {

    0%,
    100% {
        opacity: 0.3;
    }

    50% {
        opacity: 0.6;
    }
}

/* ── Sparkle icon ─────────────────────────────────── */
.animate-sparkle {
    animation: sparklePulse 2.5s ease-in-out infinite;
}

@keyframes sparklePulse {

    0%,
    100% {
        opacity: 1;
        transform: scale(1) rotate(0deg);
    }

    50% {
        opacity: 0.6;
        transform: scale(1.3) rotate(20deg);
    }
}

/* ── Logo cycle ───────────────────────────────────── */
.logo-gradient-display-static {
    background: linear-gradient(135deg, #14b8a6, #4f46e5);
    mask-size: contain;
    -webkit-mask-size: contain;
    mask-repeat: no-repeat;
    -webkit-mask-repeat: no-repeat;
    mask-position: center;
    -webkit-mask-position: center;
}

.dark .logo-gradient-display-static {
    background: linear-gradient(135deg, #5eead4, #818cf8);
    filter: drop-shadow(0 0 8px rgba(94, 234, 212, 0.3));
}

@keyframes logoCycle1 {

    0%,
    42% {
        opacity: 1;
        transform: scale(1) rotate(0deg);
    }

    48%,
    92% {
        opacity: 0;
        transform: scale(0.5) rotate(-15deg);
    }

    98%,
    100% {
        opacity: 1;
        transform: scale(1) rotate(0deg);
    }
}

@keyframes logoCycle2 {

    0%,
    42% {
        opacity: 0;
        transform: scale(0.5) rotate(15deg);
    }

    48%,
    92% {
        opacity: 1;
        transform: scale(1) rotate(0deg);
    }

    98%,
    100% {
        opacity: 0;
        transform: scale(0.5) rotate(-15deg);
    }
}

.animate-logo-cycle-1 {
    animation: logoCycle1 10s infinite;
}

.animate-logo-cycle-2 {
    animation: logoCycle2 10s infinite;
}
</style>
