import { ref } from 'vue'

const getInitialCollapsed = (): boolean => {
  const stored = localStorage.getItem('student_sidebar_collapsed')
  return stored === 'true'
}

export const isSidebarCollapsed = ref(getInitialCollapsed())

export function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
  localStorage.setItem('student_sidebar_collapsed', String(isSidebarCollapsed.value))
}
