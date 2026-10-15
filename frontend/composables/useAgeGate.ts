// Conferma della maggiore eta' all'ingresso (sito di promozione di bevande alcoliche).
// La risposta si ricorda con un cookie tecnico per 12 mesi: niente consenso aggiuntivo.
export const AGE_COOKIE = 'em_maggiore_eta'
const ONE_YEAR = 60 * 60 * 24 * 365

export const useAgeGate = () => {
  const cookie = useCookie<string | number | null>(AGE_COOKIE, {
    maxAge: ONE_YEAR,
    sameSite: 'lax',
    secure: !import.meta.dev,
    path: '/',
    default: () => null
  })
  // useCookie converte "1" nel numero 1: si confronta il testo
  const confirmed = useState<boolean>('age_confirmed', () => String(cookie.value ?? '') === '1')
  const confirm = () => {
    cookie.value = '1'
    confirmed.value = true
  }
  return { confirmed, confirm }
}
