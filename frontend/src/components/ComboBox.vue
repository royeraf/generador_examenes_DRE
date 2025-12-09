<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { ChevronDown, Check } from 'lucide-vue-next';

interface Option {
    id: number;
    label: string;
    group?: string;
}

interface Props {
    modelValue: number | null;
    options: Option[];
    placeholder?: string;
}

const props = withDefaults(defineProps<Props>(), {
    placeholder: 'Seleccionar...'
});

const emit = defineEmits<{
    (e: 'update:modelValue', value: number | null): void;
}>();

const isOpen = ref(false);
const containerRef = ref<HTMLDivElement | null>(null);

const selectedOption = computed(() =>
    props.options.find(opt => opt.id === props.modelValue)
);

const displayValue = computed(() =>
    selectedOption.value?.label || ''
);

// We no longer filter options, just use props.options directly
const groupedOptions = computed(() => {
    const groups: Record<string, Option[]> = {};
    props.options.forEach(opt => {
        const group = opt.group || 'General';
        if (!groups[group]) groups[group] = [];
        groups[group].push(opt);
    });
    return groups;
});

const hasGroups = computed(() => {
    const groupNames = Object.keys(groupedOptions.value);
    return groupNames.length > 1 || (groupNames.length === 1 && groupNames[0] !== 'General');
});

const toggleDropdown = () => {
    isOpen.value = !isOpen.value;
};

const selectOption = (option: Option) => {
    emit('update:modelValue', option.id);
    isOpen.value = false;
};

const handleClickOutside = (event: MouseEvent) => {
    if (containerRef.value && !containerRef.value.contains(event.target as Node)) {
        isOpen.value = false;
    }
};

onMounted(() => {
    document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside);
});
</script>

<template>
    <div ref="containerRef" class="relative">
        <!-- Input -->
        <div class="relative cursor-pointer" @click="toggleDropdown">
            <input type="text" readonly :value="displayValue" :placeholder="placeholder" class="w-full px-3 py-2.5 pr-9 
               bg-white dark:bg-slate-900 
               border border-slate-200 dark:border-slate-600 
               rounded-lg 
               text-slate-900 dark:text-white 
               text-sm 
               focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500
               placeholder:text-slate-400 dark:placeholder:text-slate-500 
               cursor-pointer pointer-events-none transition-colors" role="combobox" :aria-expanded="isOpen" />
            <button type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors">
                <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="{ 'rotate-180': isOpen }" />
            </button>
        </div>

        <!-- Dropdown -->
        <Transition name="dropdown">
            <div v-if="isOpen" class="absolute z-50 mt-1.5 w-full max-h-56 overflow-y-auto 
               bg-white dark:bg-slate-800 
               border border-slate-200 dark:border-slate-600 
               rounded-lg shadow-xl dark:shadow-black/30">
                <div class="p-1.5">
                    <!-- Grouped options -->
                    <template v-if="hasGroups">
                        <div v-for="(groupOptions, groupName) in groupedOptions" :key="groupName"
                            class="mb-1 last:mb-0">
                            <div
                                class="px-2 py-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                                {{ groupName }}
                            </div>
                            <div v-for="option in groupOptions" :key="option.id" @click="selectOption(option)" class="flex items-center justify-between px-3 py-2 rounded-md cursor-pointer transition-colors
                        text-sm text-slate-700 dark:text-slate-200 
                        hover:bg-slate-100 dark:hover:bg-slate-700"
                                :class="{ 'bg-indigo-50 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300': option.id === modelValue }">
                                <span>{{ option.label }}</span>
                                <Check v-if="option.id === modelValue"
                                    class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                            </div>
                        </div>
                    </template>

                    <!-- Flat options (no groups) -->
                    <template v-else>
                        <div v-for="option in props.options" :key="option.id" @click="selectOption(option)" class="flex items-center justify-between px-3 py-2 rounded-md cursor-pointer transition-colors
                     text-sm text-slate-700 dark:text-slate-200 
                     hover:bg-slate-100 dark:hover:bg-slate-700"
                            :class="{ 'bg-indigo-50 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300': option.id === modelValue }">
                            <span>{{ option.label }}</span>
                            <Check v-if="option.id === modelValue"
                                class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                        </div>
                    </template>

                    <!-- Empty state -->
                    <div v-if="props.options.length === 0"
                        class="px-3 py-4 text-center text-sm text-slate-500 dark:text-slate-400">
                        No se encontraron resultados
                    </div>
                </div>
            </div>
        </Transition>
    </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
    transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}

/* Custom Scrollbar Styles */
.overflow-y-auto::-webkit-scrollbar {
    width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
    background: transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
    background-color: #475569;
    /* slate-600 */
    border-radius: 20px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
    background-color: #64748b;
    /* slate-500 */
}
</style>
