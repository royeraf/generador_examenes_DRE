<script setup lang="ts">
import { computed } from 'vue';
import { FileText, FileType2, File } from 'lucide-vue-next';
import { getFileKind } from '../utils/uploadFeedback';

const props = withDefaults(defineProps<{
  filename?: string;
  extension?: string;
  size?: 'sm' | 'md';
}>(), {
  filename: '',
  extension: '',
  size: 'sm',
});

const kind = computed(() => getFileKind(props.extension || props.filename || ''));

const icon = computed(() => {
  if (kind.value === 'pdf') return FileText;
  if (kind.value === 'word') return FileType2;
  return File;
});

const colorClasses = computed(() => {
  if (kind.value === 'pdf') return 'bg-red-500/10 text-red-500 dark:text-red-400';
  if (kind.value === 'word') return 'bg-blue-500/10 text-blue-500 dark:text-blue-400';
  return 'bg-slate-500/10 text-slate-400';
});

const boxClasses = computed(() => props.size === 'md' ? 'w-9 h-9 rounded-lg' : 'w-6 h-6 rounded-md');
const iconClasses = computed(() => props.size === 'md' ? 'w-4 h-4' : 'w-3.5 h-3.5');
</script>

<template>
  <span class="inline-flex items-center justify-center shrink-0" :class="[boxClasses, colorClasses]">
    <component :is="icon" :class="iconClasses" />
  </span>
</template>
