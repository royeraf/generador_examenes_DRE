import { shallowRef, watch } from 'vue';

export type ThemeMode = 'light' | 'dark' | 'system';

// --- Estado global del módulo ---
const getInitialMode = (): ThemeMode => {
  if (typeof window === 'undefined') return 'dark';
  const saved = localStorage.getItem('themeMode') as ThemeMode | null;
  if (saved === 'light' || saved === 'dark' || saved === 'system') return saved;
  // Fallback: si había guardado el tema viejo (boolean)
  const oldSaved = localStorage.getItem('theme');
  if (oldSaved === 'light') return 'light';
  return 'system';
};

const themeMode = shallowRef<ThemeMode>(getInitialMode());

// Listener para cambios del sistema operativo
let systemMediaQuery: MediaQueryList | null = null;
const systemChangeHandler = () => applyThemeClass();

const applyThemeClass = () => {
  if (typeof document === 'undefined') return;
  const mode = themeMode.value;

  let isDark: boolean;
  if (mode === 'system') {
    if (!systemMediaQuery) {
      systemMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      systemMediaQuery.addEventListener('change', systemChangeHandler);
    }
    isDark = systemMediaQuery.matches;
  } else {
    // Cuando el modo no es 'system', ya no necesitamos el listener
    if (systemMediaQuery) {
      systemMediaQuery.removeEventListener('change', systemChangeHandler);
      systemMediaQuery = null;
    }
    isDark = mode === 'dark';
  }

  document.documentElement.classList.toggle('dark', isDark);
  localStorage.setItem('themeMode', mode);
};

// Aplicar al cargar
applyThemeClass();

watch(themeMode, () => applyThemeClass());

export function useTheme() {
  const setMode = (mode: ThemeMode) => {
    themeMode.value = mode;
  };

  // Compatibilidad con el Header que usa toggleTheme + isDark
  const isDark = shallowRef(document.documentElement.classList.contains('dark'));
  watch(themeMode, () => {
    isDark.value = document.documentElement.classList.contains('dark');
  });

  const toggleTheme = () => {
    const current = themeMode.value;
    if (current === 'light') themeMode.value = 'dark';
    else if (current === 'dark') themeMode.value = 'system';
    else themeMode.value = 'light';
  };

  return { themeMode, isDark, setMode, toggleTheme };
}
