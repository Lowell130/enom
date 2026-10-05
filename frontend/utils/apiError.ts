// Messaggio leggibile da mostrare all'utente per un errore delle API.
// Il backend restituisce gia' frasi in italiano in "detail" (anche per i dati non validi, errore 422).
export const apiErrorMessage = (err: any, fallback = 'Si è verificato un errore. Riprova.'): string => {
  if (!err) return fallback
  if (!err.status && !err.statusCode && !err.data) {
    return 'Il server non risponde. Controlla la connessione e riprova tra poco.'
  }
  const detail = err.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail) && detail.length) {
    const first = detail[0]
    if (typeof first?.msg === 'string') return first.msg.replace(/^Value error, /, '')
  }
  if (err.status === 429) return 'Troppe richieste in poco tempo. Riprova tra qualche minuto.'
  return fallback
}
