import { shallowRef, watch } from 'vue';

// Check if we should be in dark mode
const getInitialTheme = (): boolean => {
  if (typeof window === 'undefined') return true;

  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    return savedTheme === 'dark';
  }
  // Default to dark if no preference or system prefers dark
  return window.matchMedia('(prefers-color-scheme: dark)').matches || true;
};

const isDark = shallowRef(getInitialTheme());

// Apply theme class to document
const applyThemeClass = () => {
  if (typeof document === 'undefined') return;
  
  if (isDark.value) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light');
};

// Apply the theme immediately when this module loads
applyThemeClass();

// Watch for changes to isDark and apply the theme class
watch(isDark, () => {
  applyThemeClass();
});

export function useTheme() {
  const toggleTheme = () => {
    isDark.value = !isDark.value;
  };

  return {
    isDark,
    toggleTheme
  };
}
