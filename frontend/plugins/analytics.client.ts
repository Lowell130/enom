// Google Analytics 4, solo con il consenso ai cookie di statistica.
// - L'ID (G-XXXX) arriva dall'area admin; senza ID non si carica nulla.
// - Lo script di Google si aggiunge solo dopo "Accetta" (o statistiche attivate nelle preferenze).
// - Se il consenso viene revocato: tracciamento disattivato e cookie _ga cancellati.
// - Niente statistiche per chi e' collegato all'area riservata (amministratore e cantine).

declare global {
  interface Window {
    dataLayer: any[]
    gtag?: (...args: any[]) => void
    [key: `ga-disable-${string}`]: boolean
  }
}

const THIRTEEN_MONTHS = 60 * 60 * 24 * 395

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()
  const gaId = useAnalyticsId()
  const { allows } = useCookieConsent()
  const authCookie = useCookie('auth_token')
  let loadedId = ''

  const deleteGaCookies = () => {
    const host = location.hostname
    const domains = ['', host, '.' + host, '.' + host.split('.').slice(-2).join('.')]
    for (const c of document.cookie.split(';')) {
      const name = c.split('=')[0].trim()
      if (name === '_ga' || name.startsWith('_ga_') || name === '_gid') {
        for (const d of domains) {
          document.cookie = `${name}=; Max-Age=0; path=/${d ? '; domain=' + d : ''}`
        }
      }
    }
  }

  const start = (id: string) => {
    window[`ga-disable-${id}`] = false
    if (loadedId === id) {
      window.gtag?.('consent', 'update', { analytics_storage: 'granted' })
      return
    }
    loadedId = id
    window.dataLayer = window.dataLayer || []
    window.gtag = function gtag () { window.dataLayer.push(arguments) }
    window.gtag('consent', 'default', {
      analytics_storage: 'granted',
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied'
    })
    window.gtag('js', new Date())
    window.gtag('config', id, {
      allow_google_signals: false,
      allow_ad_personalization_signals: false,
      cookie_expires: THIRTEEN_MONTHS
    })
    const s = document.createElement('script')
    s.async = true
    s.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(id)}`
    document.head.appendChild(s)
  }

  const stop = () => {
    if (loadedId) {
      window[`ga-disable-${loadedId}`] = true
      window.gtag?.('consent', 'update', { analytics_storage: 'denied' })
    }
    deleteGaCookies()
  }

  const apply = () => {
    const id = gaId.value
    const ok = !!id && allows('statistiche') && !authCookie.value
    if (ok) start(id)
    else stop()
  }

  // ID letto una volta all'avvio; se il server non risponde le statistiche restano spente
  $fetch<{ ga_measurement_id?: string }>(`${config.public.apiBase}/site/analytics`)
    .then((res) => { gaId.value = res?.ga_measurement_id || '' })
    .catch(() => { gaId.value = '' })

  watch([gaId, () => allows('statistiche'), () => authCookie.value], apply)
})
