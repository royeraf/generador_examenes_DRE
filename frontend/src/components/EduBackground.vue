<script setup lang="ts">
import {
    BookOpen,
    Pencil,
    Star,
    GraduationCap,
    Calculator,
    Globe,
    Trophy,
    Atom,
    Palette,
    Layers,
    FileQuestion,
    Medal,
    Music,
    Compass,
    Microscope,
    Ruler,
    PenTool,
    Shapes,
    Puzzle,
    Wand2,
    Infinity,
    Sigma
} from 'lucide-vue-next';

interface Props {
    variant?: 'teal' | 'indigo' | 'violet' | 'emerald';
}

const props = withDefaults(defineProps<Props>(), {
    variant: 'teal'
});

const circleColors = {
    teal: {
        c1: 'bg-teal-200/40 dark:bg-teal-500/10',
        c2: 'bg-amber-200/40 dark:bg-amber-500/10',
        c3: 'bg-sky-200/30 dark:bg-sky-500/10',
        c4: 'bg-violet-200/20 dark:bg-violet-500/5',
        c5: 'bg-rose-200/20 dark:bg-rose-500/5',
        c6: 'bg-emerald-200/25 dark:bg-emerald-500/5'
    },
    indigo: {
        c1: 'bg-indigo-200/40 dark:bg-indigo-500/10',
        c2: 'bg-purple-200/40 dark:bg-purple-500/10',
        c3: 'bg-blue-200/30 dark:bg-blue-500/10',
        c4: 'bg-fuchsia-200/20 dark:bg-fuchsia-500/5',
        c5: 'bg-teal-200/20 dark:bg-teal-500/5',
        c6: 'bg-violet-200/25 dark:bg-violet-500/5'
    },
    violet: {
        c1: 'bg-violet-200/40 dark:bg-violet-500/10',
        c2: 'bg-purple-200/40 dark:bg-purple-500/10',
        c3: 'bg-indigo-200/30 dark:bg-indigo-500/10',
        c4: 'bg-pink-200/20 dark:bg-pink-500/5',
        c5: 'bg-blue-200/20 dark:bg-blue-500/5',
        c6: 'bg-slate-200/25 dark:bg-slate-500/5'
    },
    emerald: {
        c1: 'bg-emerald-200/40 dark:bg-emerald-500/10',
        c2: 'bg-teal-200/40 dark:bg-teal-500/10',
        c3: 'bg-lime-200/30 dark:bg-lime-500/10',
        c4: 'bg-sky-200/20 dark:bg-sky-500/5',
        c5: 'bg-amber-200/20 dark:bg-amber-500/5',
        c6: 'bg-teal-200/25 dark:bg-teal-500/5'
    }
};

const colors = circleColors[props.variant];
</script>

<template>
    <div class="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <!-- Animated Circles -->
        <div :class="['absolute -top-24 -right-24 w-96 h-96 rounded-full blur-3xl animate-float', colors.c1]"></div>
        <div :class="['absolute top-1/3 -left-24 w-80 h-80 rounded-full blur-3xl', colors.c2]"
            style="animation-delay: 2s;"></div>
        <div :class="['absolute bottom-0 right-1/4 w-72 h-72 rounded-full blur-3xl animate-float', colors.c3]"
            style="animation-delay: 4s;"></div>
        <div :class="['absolute top-2/3 left-1/3 w-64 h-64 rounded-full blur-3xl', colors.c4]"></div>
        <div :class="['absolute top-1/4 right-1/3 w-48 h-48 rounded-full blur-3xl animate-float', colors.c5]"
            style="animation-delay: 6s;"></div>
        <div :class="['absolute bottom-1/4 left-1/4 w-56 h-56 rounded-full blur-3xl', colors.c6]"
            style="animation-delay: 3.5s;"></div>

        <!-- Floating Educational Icons -->
        <div class="absolute top-20 right-[15%] text-teal-400/30 dark:text-teal-500/15 animate-float">
            <BookOpen class="w-16 h-16" />
        </div>
        <div class="absolute top-[40%] left-[8%] text-amber-400/30 dark:text-amber-500/15 animate-float"
            style="animation-delay: 3s;">
            <Pencil class="w-12 h-12" />
        </div>
        <div class="absolute bottom-[20%] right-[10%] text-sky-400/30 dark:text-sky-500/15 animate-float"
            style="animation-delay: 1s;">
            <Star class="w-14 h-14" />
        </div>
        <div class="absolute bottom-[35%] left-[20%] text-violet-400/25 dark:text-violet-500/12 animate-float"
            style="animation-delay: 5s;">
            <GraduationCap class="w-10 h-10" />
        </div>
        <div class="absolute top-[15%] left-[25%] text-emerald-400/25 dark:text-emerald-500/12 animate-float"
            style="animation-delay: 2.5s;">
            <Calculator class="w-10 h-10" />
        </div>
        <div class="absolute top-[55%] right-[20%] text-rose-400/25 dark:text-rose-500/12 animate-float"
            style="animation-delay: 4.5s;">
            <Globe class="w-12 h-12" />
        </div>
        <div class="absolute bottom-[45%] right-[35%] text-amber-400/25 dark:text-amber-500/12 animate-float"
            style="animation-delay: 1.5s;">
            <Trophy class="w-9 h-9" />
        </div>
        <div class="absolute top-[70%] left-[12%] text-cyan-400/25 dark:text-cyan-500/12 animate-float"
            style="animation-delay: 6.5s;">
            <Atom class="w-11 h-11" />
        </div>
        <div class="absolute top-[30%] right-[8%] text-pink-400/25 dark:text-pink-500/12 animate-float"
            style="animation-delay: 3.5s;">
            <Palette class="w-10 h-10" />
        </div>
        <div class="absolute bottom-[15%] left-[40%] text-indigo-400/25 dark:text-indigo-500/12 animate-float"
            style="animation-delay: 7s;">
            <Layers class="w-8 h-8" />
        </div>
        <div class="absolute top-[85%] right-[25%] text-teal-400/20 dark:text-teal-500/10 animate-float"
            style="animation-delay: 5.5s;">
            <FileQuestion class="w-9 h-9" />
        </div>
        <div class="absolute top-[10%] left-[45%] text-amber-400/20 dark:text-amber-500/10 animate-float"
            style="animation-delay: 8s;">
            <Medal class="w-8 h-8" />
        </div>
        <div class="absolute top-[5%] right-[40%] text-purple-400/25 dark:text-purple-500/12 animate-float"
            style="animation-delay: 2s;">
            <Music class="w-9 h-9" />
        </div>
        <div class="absolute top-[45%] left-[5%] text-blue-400/25 dark:text-blue-500/12 animate-float"
            style="animation-delay: 4s;">
            <Compass class="w-11 h-11" />
        </div>
        <div class="absolute top-[60%] right-[5%] text-green-400/25 dark:text-green-500/12 animate-float"
            style="animation-delay: 9s;">
            <Microscope class="w-12 h-12" />
        </div>
        <div class="absolute bottom-[8%] left-[15%] text-orange-400/25 dark:text-orange-500/12 animate-float"
            style="animation-delay: 6s;">
            <Ruler class="w-10 h-10" />
        </div>
        <div class="absolute top-[20%] left-[65%] text-red-400/20 dark:text-red-500/10 animate-float"
            style="animation-delay: 3s;">
            <PenTool class="w-8 h-8" />
        </div>
        <div class="absolute bottom-[55%] right-[45%] text-cyan-400/20 dark:text-cyan-500/10 animate-float"
            style="animation-delay: 7.5s;">
            <Shapes class="w-9 h-9" />
        </div>
        <div class="absolute top-[75%] left-[55%] text-lime-400/25 dark:text-lime-500/12 animate-float"
            style="animation-delay: 1.5s;">
            <Puzzle class="w-11 h-11" />
        </div>
        <div class="absolute bottom-[40%] left-[70%] text-fuchsia-400/25 dark:text-fuchsia-500/12 animate-float"
            style="animation-delay: 8.5s;">
            <Wand2 class="w-8 h-8" />
        </div>
        <div class="absolute top-[50%] right-[55%] text-sky-400/20 dark:text-sky-500/10 animate-float"
            style="animation-delay: 4.5s;">
            <Infinity class="w-10 h-10" />
        </div>
        <div class="absolute bottom-[25%] right-[60%] text-violet-400/20 dark:text-violet-500/10 animate-float"
            style="animation-delay: 10s;">
            <Sigma class="w-9 h-9" />
        </div>
    </div>
</template>

<style scoped>
@keyframes float {

    0%,
    100% {
        transform: translateY(0) rotate(0);
    }

    50% {
        transform: translateY(-20px) rotate(5deg);
    }
}

.animate-float {
    animation: float 6s ease-in-out infinite;
}

.edu-pattern-bg {
    background-image: radial-gradient(#94a3b8 0.5px, transparent 0.5px);
    background-size: 24px 24px;
}
</style>
