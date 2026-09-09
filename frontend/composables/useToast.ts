import { ref } from 'vue'

export interface ToastMessage {
  id: string
  title?: string
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
  duration?: number
}

const toasts = ref<ToastMessage[]>([])

export const useToast = () => {
  const addToast = (toast: Omit<ToastMessage, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast: ToastMessage = {
      id,
      duration: toast.duration || 4000,
      ...toast
    }
    toasts.value.push(newToast)

    if (newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, newToast.duration)
    }
  }

  const removeToast = (id: string) => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  const success = (message: string, title: string = 'Operazione completata') => {
    addToast({ title, message, type: 'success' })
  }

  const error = (message: string, title: string = 'Si è verificato un errore') => {
    addToast({ title, message, type: 'error', duration: 5000 })
  }

  const info = (message: string, title: string = 'Informazione') => {
    addToast({ title, message, type: 'info' })
  }

  const warning = (message: string, title: string = 'Attenzione') => {
    addToast({ title, message, type: 'warning' })
  }

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    info,
    warning
  }
}
