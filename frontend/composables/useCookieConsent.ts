// Consenso ai cookie (linee guida del Garante, giugno 2021):
// - i cookie tecnici non chiedono consenso, tutto il resto parte spento;
// - "Rifiuta" e la X valgono come rifiuto, la scelta resta valida 6 mesi;
// - le preferenze si riaprono dal link "Preferenze cookie" nel footer.
// Se un domani si aggiungono statistiche o servizi di terze parti, si caricano solo quando
// allows('statistiche') e' vero; cambiando le categorie si alza CONSENT_VERSION e la domanda
// viene riproposta a tutti.

export const CONSENT_VERSION = 1
export const CONSENT_COOKIE = 'em_consenso_cookie'
const SIX_MONTHS = 60 * 60 * 24 * 180

export type CookieCategory = 'statistiche'

export interface CookieConsent {
  v: number
  statistiche: boolean
  at: string
}

export const useCookieConsent = () => {
  const cookie = useCookie<CookieConsent | null>(CONSENT_COOKIE, {
    maxAge: SIX_MONTHS,
    sameSite: 'lax',
    secure: !import.meta.dev,
    path: '/',
    default: () => null
  })
  // stato condiviso: banner e footer vedono subito la stessa scelta
  const consent = useState<CookieConsent | null>('cookie_consent', () => cookie.value || null)
  const panelOpen = useState<boolean>('cookie_panel_open', () => false)

  const decided = computed(() => !!consent.value && consent.value.v === CONSENT_VERSION)
  const allows = (category: CookieCategory) => decided.value && !!consent.value?.[category]

  const save = (choices: { statistiche: boolean }) => {
    const value: CookieConsent = { v: CONSENT_VERSION, statistiche: !!choices.statistiche, at: new Date().toISOString() }
    consent.value = value
    cookie.value = value
    panelOpen.value = false
  }

  return {
    consent,
    decided,
    allows,
    panelOpen,
    acceptAll: () => save({ statistiche: true }),
    rejectAll: () => save({ statistiche: false }),
    save,
    openPreferences: () => { panelOpen.value = true }
  }
}
