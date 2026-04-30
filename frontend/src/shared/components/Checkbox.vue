<script setup lang="ts">
import { computed } from 'vue';

defineOptions({
    inheritAttrs: false
});

const props = defineProps<{
    modelValue?: boolean | any[];
    value?: any;
    label?: string;
    legend?: string;
    checked?: boolean;
    color?: string;
}>();

const emit = defineEmits(['update:modelValue', 'change']);

const isChecked = computed({
    get() {
        if (props.modelValue !== undefined) {
            if (Array.isArray(props.modelValue)) {
                return props.modelValue.includes(props.value);
            }
            return props.modelValue;
        }
        return props.checked;
    },
    set(val) {
        if (props.modelValue !== undefined) {
            if (Array.isArray(props.modelValue)) {
                const newValue = [...props.modelValue];
                if (val) {
                    if (!newValue.includes(props.value)) {
                        newValue.push(props.value);
                    }
                } else {
                    const index = newValue.indexOf(props.value);
                    if (index > -1) newValue.splice(index, 1);
                }
                emit('update:modelValue', newValue);
            } else {
                emit('update:modelValue', val);
            }
        } else {
            emit('change', val);
        }
    }
});
</script>

<template>
    <fieldset v-if="legend" v-bind="$attrs"
        class="fieldset border border-gray-200 dark:border-slate-700 rounded-xl p-4 bg-white dark:bg-slate-800">
        <legend class="px-2 text-sm font-bold text-slate-500 dark:text-slate-400">
            {{ legend }}
        </legend>

        <label class="flex gap-3 cursor-pointer group relative" :class="$attrs.class || 'items-center'">
            <div class="relative flex items-center justify-center h-5 w-5 mt-0.5">
                <input type="checkbox" v-model="isChecked" :value="value"
                    class="peer appearance-none w-5 h-5 rounded-md border-2 border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-white dark:focus:ring-offset-slate-900"
                    :class="[
                        color || 'checked:bg-teal-600 checked:border-teal-600 dark:checked:bg-teal-500 dark:checked:border-teal-500 focus:ring-teal-500/50'
                    ]" />
                <svg class="w-3.5 h-3.5 absolute text-white pointer-events-none opacity-0 peer-checked:opacity-100 transition-all duration-200 scale-50 peer-checked:scale-100 transform"
                    fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
            </div>

            <div class="flex-1 min-w-0 select-none">
                <span v-if="label" class="text-sm font-medium text-slate-700 dark:text-slate-300">{{ label }}</span>
                <slot />
            </div>
        </label>
    </fieldset>

    <label v-else class="flex gap-3 cursor-pointer group relative" :class="$attrs.class || 'items-center'">
        <div class="relative flex items-center justify-center h-5 w-5 mt-0.5">
            <input type="checkbox" v-model="isChecked" :value="value"
                class="peer appearance-none w-5 h-5 rounded-md border-2 border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-white dark:focus:ring-offset-slate-900"
                :class="[
                    color || 'checked:bg-teal-600 checked:border-teal-600 dark:checked:bg-teal-500 dark:checked:border-teal-500 focus:ring-teal-500/50'
                ]" />
            <svg class="w-3.5 h-3.5 absolute text-white pointer-events-none opacity-0 peer-checked:opacity-100 transition-all duration-200 scale-50 peer-checked:scale-100 transform"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
        </div>

        <div class="flex-1 min-w-0 select-none">
            <span v-if="label" class="text-sm font-medium text-slate-700 dark:text-slate-300">{{ label }}</span>
            <slot />
        </div>
    </label>
</template>
