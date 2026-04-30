import Swal from 'sweetalert2';

const swal = Swal.mixin({
  customClass: {
    popup: 'rounded-2xl',
    confirmButton: 'px-5 py-2.5 rounded-xl font-bold text-sm',
    cancelButton: 'px-5 py-2.5 rounded-xl font-bold text-sm',
  },
  buttonsStyling: true,
});

export function showSuccess(title: string, text?: string) {
  return swal.fire({
    icon: 'success',
    title,
    text,
    timer: 2500,
    showConfirmButton: false,
  });
}

export function showError(title: string, text?: string) {
  return swal.fire({
    icon: 'error',
    title,
    text,
    confirmButtonColor: '#ef4444',
  });
}

export function showWarning(title: string, text?: string) {
  return swal.fire({
    icon: 'warning',
    title,
    text,
    confirmButtonColor: '#f59e0b',
  });
}

export function showInfo(title: string, text?: string) {
  return swal.fire({
    icon: 'info',
    title,
    text,
    confirmButtonColor: '#3b82f6',
  });
}

export async function showConfirm(
  title: string,
  text: string,
  confirmText = 'Sí, continuar',
  cancelText = 'Cancelar'
): Promise<boolean> {
  const result = await swal.fire({
    icon: 'warning',
    title,
    text,
    showCancelButton: true,
    confirmButtonColor: '#14b8a6',
    cancelButtonColor: '#94a3b8',
    confirmButtonText: confirmText,
    cancelButtonText: cancelText,
  });
  return result.isConfirmed;
}

export async function showDeleteConfirm(
  title = '¿Estás seguro?',
  text = 'Esta acción no se puede deshacer'
): Promise<boolean> {
  const result = await swal.fire({
    icon: 'warning',
    title,
    text,
    showCancelButton: true,
    confirmButtonColor: '#ef4444',
    cancelButtonColor: '#94a3b8',
    confirmButtonText: 'Sí, eliminar',
    cancelButtonText: 'Cancelar',
  });
  return result.isConfirmed;
}

export const Toast = Swal.mixin({
  toast: true,
  position: 'top-end',
  showConfirmButton: false,
  timer: 3000,
  timerProgressBar: true,
  didOpen: (toast) => {
    toast.onmouseenter = Swal.stopTimer;
    toast.onmouseleave = Swal.resumeTimer;
  },
});
