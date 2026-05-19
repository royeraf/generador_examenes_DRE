<!-- Header.vue — alias de Navbar para compatibilidad con vistas existentes -->
<script setup lang="ts">
import Navbar from './Navbar.vue';

interface Props {
  title: string;
  subtitle?: string;
  showResults?: boolean;
  hasResultado?: boolean;
  loading?: boolean;
  activeTab?: string;
  gradientClass?: string;
  subtitleClass?: string;
  isDark?: boolean;
}
withDefaults(defineProps<Props>(), {
  subtitle: '',
  showResults: false,
  hasResultado: false,
  loading: false,
  activeTab: 'generador',
  gradientClass: '',
  subtitleClass: '',
  isDark: false,
});
defineEmits(['toggleTheme', 'toggleResults']);
</script>

<template>
  <Navbar :title="title" :subtitle="subtitle">
    <template #actions>
      <slot name="actions-before" />
      <slot name="actions-after" />
    </template>
  </Navbar>
</template>
