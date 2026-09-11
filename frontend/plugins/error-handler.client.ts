export default defineNuxtPlugin((nuxtApp) => {
  if (process.client) {
    // 1. Intercept global unhandled window errors (e.g., from browser extensions or injected performance scripts)
    window.addEventListener(
      'error',
      (event) => {
        const msg = event.message || event.error?.message || ''
        const stack = event.error?.stack || ''
        const filename = event.filename || ''

        // Suppress browser extension / performance observer errors such as 'reading startTime' or 'reportAllChanges'
        if (
          msg.includes("reading 'startTime'") ||
          msg.includes('reportAllChanges') ||
          msg.includes('startTime') ||
          stack.includes('reportAllChanges')
        ) {
          event.stopImmediatePropagation()
          event.preventDefault()
          return true
        }
      },
      true
    )

    // 2. Intercept unhandled promise rejections
    window.addEventListener(
      'unhandledrejection',
      (event) => {
        const reason = event.reason
        const msg = typeof reason === 'string' ? reason : reason?.message || ''
        if (
          msg.includes("reading 'startTime'") ||
          msg.includes('reportAllChanges') ||
          msg.includes('startTime')
        ) {
          event.stopImmediatePropagation()
          event.preventDefault()
        }
      },
      true
    )

    // 3. Nuxt Vue Error Handler to prevent Vue event handler warnings
    nuxtApp.vueApp.config.errorHandler = (err, instance, info) => {
      const msg = (err as Error)?.message || ''
      const stack = (err as Error)?.stack || ''

      if (
        msg.includes("reading 'startTime'") ||
        msg.includes('reportAllChanges') ||
        msg.includes('startTime') ||
        stack.includes('reportAllChanges')
      ) {
        return
      }

      console.error('[Vue Handler Error]:', err, info)
    }
  }
})
