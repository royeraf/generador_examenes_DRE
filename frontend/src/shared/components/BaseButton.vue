<script setup lang="ts">
import { computed } from 'vue';
import { Loader2 } from 'lucide-vue-next';

interface Props {
    variant?: 'primary' | 'secondary' | 'destructive';
    size?: 'xs' | 'sm' | 'md' | 'lg';
    type?: 'button' | 'submit' | 'reset';
    disabled?: boolean;
    loading?: boolean;
    block?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    variant: 'primary',
    size: 'md',
    type: 'button',
    disabled: false,
    loading: false,
    block: false,
});

const variantClasses: Record<NonNullable<Props['variant']>, string> = {
    primary: 'bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-600 hover:to-emerald-700 text-white shadow-xl shadow-teal-500/20',
    secondary: 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-2 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700',
    destructive: 'bg-red-500 hover:bg-red-600 text-white shadow-xl shadow-red-500/20',
};

const sizeClasses: Record<NonNullable<Props['size']>, string> = {
    xs: 'px-2.5 py-1.5 text-[10px] gap-1 rounded-lg font-bold',
    sm: 'px-4 py-2.5 text-[10px] gap-2 rounded-2xl font-black uppercase tracking-widest',
    md: 'px-6 py-3.5 text-xs gap-3 rounded-2xl font-black uppercase tracking-widest',
    lg: 'px-8 py-4 text-xs gap-3 rounded-2xl font-black uppercase tracking-widest',
};

const iconSizeClasses: Record<NonNullable<Props['size']>, string> = {
    xs: 'w-3.5 h-3.5',
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
};

const classes = computed(() => [
    'inline-flex items-center justify-center transition-all active:scale-95 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100',
    variantClasses[props.variant],
    sizeClasses[props.size],
    props.block ? 'w-full' : '',
]);
</script>

<template>
    <button :type="type" :disabled="disabled || loading" :class="classes">
        <Loader2 v-if="loading" :class="[iconSizeClasses[size], 'animate-spin shrink-0']" />
        <slot v-else name="icon" />
        <slot />
    </button>
</template>
