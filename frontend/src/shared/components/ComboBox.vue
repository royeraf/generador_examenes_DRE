<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { ChevronDown, Check, School, BookOpen } from 'lucide-vue-next';

interface Option {
    id: number | string | null;
    label: string;
    group?: string;
}

interface Props {
    modelValue: number | string | null;
    options: Option[];
    placeholder?: string;
    disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
    placeholder: 'Seleccionar...',
    disabled: false,
});

const emit = defineEmits<{
    (e: 'update:modelValue', value: number | string | null): void;
}>();

const isOpen = ref(false);
const dropUp = ref(false);
const containerRef = ref<HTMLDivElement | null>(null);
const dropdownRef = ref<HTMLDivElement | null>(null);

interface DropdownStyle {
    position: 'fixed';
    top?: string;
    bottom?: string;
    left: string;
    width: string;
}
const dropdownStyle = ref<DropdownStyle>({ position: 'fixed', left: '0px', width: '0px' });

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

const DROPDOWN_HEIGHT = 260; // max-h-60 (240px) + padding
const GAP = 8;

const toggleDropdown = () => {
    if (props.disabled) return;
    if (!isOpen.value && containerRef.value) {
        const rect = containerRef.value.getBoundingClientRect();
        const spaceBelow = window.innerHeight - rect.bottom;
        const spaceAbove = rect.top;
        dropUp.value = spaceBelow < DROPDOWN_HEIGHT && spaceAbove > spaceBelow;

        if (dropUp.value) {
            dropdownStyle.value = {
                position: 'fixed',
                bottom: `${window.innerHeight - rect.top + GAP}px`,
                left: `${rect.left}px`,
                width: `${rect.width}px`,
            };
        } else {
            dropdownStyle.value = {
                position: 'fixed',
                top: `${rect.bottom + GAP}px`,
                left: `${rect.left}px`,
                width: `${rect.width}px`,
            };
        }
    }
    isOpen.value = !isOpen.value;
};

const selectOption = (option: Option) => {
    emit('update:modelValue', option.id);
    isOpen.value = false;
};

const handleClickOutside = (event: MouseEvent) => {
    const target = event.target as Node;
    const insideTrigger = containerRef.value?.contains(target) ?? false;
    const insideDropdown = dropdownRef.value?.contains(target) ?? false;
    if (!insideTrigger && !insideDropdown) {
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
        <div class="relative" :class="disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'" @click="toggleDropdown">
            <input type="text" readonly :value="displayValue" :placeholder="placeholder" class="w-full px-4 py-3 pr-10
               bg-white dark:bg-[#121212]
               border-2 border-slate-300 dark:border-slate-600
               rounded-xl
               text-slate-900 dark:text-white
               text-sm font-medium
               focus:outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20
               placeholder:text-slate-400 dark:placeholder:text-slate-500
               pointer-events-none transition-all duration-300"
               :class="disabled ? 'cursor-not-allowed' : 'cursor-pointer hover:border-teal-400'"
               role="combobox" :aria-expanded="isOpen" />
            <button type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-lg bg-teal-100 dark:bg-emerald-900/30 text-teal-600 dark:text-emerald-400 flex items-center justify-center transition-all duration-300"
                :class="{ 'bg-teal-500 text-white': isOpen }">
                <ChevronDown class="w-4 h-4 transition-transform duration-300" :class="{ 'rotate-180': isOpen }" />
            </button>
        </div>

    </div>

    <!-- Dropdown — teleported to body to escape modal overflow -->
    <Teleport to="body">
        <Transition :name="dropUp ? 'dropdown-up' : 'dropdown'">
            <div v-if="isOpen" ref="dropdownRef"
                class="max-h-60 overflow-y-auto
                   bg-white dark:bg-[#252525]
                   border-2 border-teal-200 dark:border-slate-600
                   rounded-xl shadow-xl shadow-teal-500/10 dark:shadow-black/30"
                :style="{ ...dropdownStyle, zIndex: 9999 }">
                <div class="p-2">
                    <!-- Grouped options -->
                    <template v-if="hasGroups">
                        <div v-for="(groupOptions, groupName) in groupedOptions" :key="groupName"
                            class="mb-2 last:mb-0">
                            <div
                                class="px-3 py-2 text-xs font-bold text-teal-600 dark:text-emerald-400 uppercase tracking-wider bg-teal-50 dark:bg-emerald-900/20 rounded-lg mb-1 flex items-center gap-2">
                                <School class="w-3.5 h-3.5" />
                                {{ groupName }}
                            </div>
                            <div v-for="option in groupOptions" :key="String(option.id)" @click="selectOption(option)"
                                class="flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200
                                text-sm text-slate-700 dark:text-slate-200 font-medium
                                hover:bg-teal-50 dark:hover:bg-slate-700"
                                :class="{ 'bg-gradient-to-r from-teal-50 to-sky-50 dark:bg-none dark:bg-emerald-500/20 text-teal-700 dark:text-emerald-300 border-l-4 border-teal-500': option.id === modelValue }">
                                <span>{{ option.label }}</span>
                                <Check v-if="option.id === modelValue" class="w-5 h-5 text-teal-600 dark:text-emerald-400" />
                            </div>
                        </div>
                    </template>

                    <!-- Flat options (no groups) -->
                    <template v-else>
                        <div v-for="option in props.options" :key="String(option.id)" @click="selectOption(option)"
                            class="flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200
                            text-sm text-slate-700 dark:text-slate-200 font-medium
                            hover:bg-teal-50 dark:hover:bg-slate-700"
                            :class="{ 'bg-gradient-to-r from-teal-50 to-sky-50 dark:bg-none dark:bg-emerald-500/20 text-teal-700 dark:text-emerald-300 border-l-4 border-teal-500': option.id === modelValue }">
                            <span>{{ option.label }}</span>
                            <Check v-if="option.id === modelValue" class="w-5 h-5 text-teal-600 dark:text-emerald-400" />
                        </div>
                    </template>

                    <!-- Empty state -->
                    <div v-if="props.options.length === 0" class="px-4 py-6 text-center">
                        <div class="w-12 h-12 bg-amber-100 dark:bg-amber-900/30 rounded-xl flex items-center justify-center mx-auto mb-2">
                            <BookOpen class="w-6 h-6 text-amber-500 dark:text-amber-400" />
                        </div>
                        <p class="text-sm text-slate-500 dark:text-slate-400 font-medium">No se encontraron resultados</p>
                    </div>
                </div>
            </div>
        </Transition>
    </Teleport>
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

.dropdown-up-enter-active,
.dropdown-up-leave-active {
    transition: all 0.2s ease;
}

.dropdown-up-enter-from,
.dropdown-up-leave-to {
    opacity: 0;
    transform: translateY(8px);
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
