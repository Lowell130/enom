// Numero per wa.me: solo cifre, con prefisso internazionale.
// "337 667 7760" -> "393376677760"; "+39 333..." e "0039 333..." restano italiani;
// "0874 123456" (fisso) -> "390874123456"; "+33 6..." (estero, con il +) resta com'e'.
// Senza questa correzione wa.me legge "33..." come Francia e "34..." come Spagna.
export const normalizeWhatsAppNumber = (raw?: string): string => {
  const value = String(raw || '').trim()
  if (!value) return ''
  let digits = value.replace(/\D/g, '')
  if (!digits) return ''
  if (digits.startsWith('00')) return digits.slice(2)          // 0039..., 0033...
  if (value.startsWith('+')) return digits                      // prefisso gia' indicato
  if (digits.startsWith('39') && digits.length >= 11) return digits
  if (/^[03]/.test(digits)) return '39' + digits                // cellulare o fisso italiano
  return digits
}

export const useWhatsApp = () => {
  const getWhatsAppUrl = (options: {
    number?: string
    companyName?: string
    productName?: string
  }): string => {
    if (!options.number) return '#'
    const cleanNumber = normalizeWhatsAppNumber(options.number)
    if (!cleanNumber) return '#'

    let text = ''
    if (options.productName) {
      text = `Salve! Ho visto il vino "${options.productName}"${options.companyName ? ` della cantina ${options.companyName}` : ''} su EnotecaMolise.it e vorrei maggiori informazioni.`
    } else if (options.companyName) {
      text = `Salve! Ho visto la scheda di ${options.companyName} su EnotecaMolise.it e vorrei maggiori informazioni.`
    } else {
      text = `Salve! Vi contatto da EnotecaMolise.it e vorrei maggiori informazioni sui vostri vini.`
    }

    return `https://wa.me/${cleanNumber}?text=${encodeURIComponent(text)}`
  }

  const formatWebsiteUrl = (url?: string): string => {
    if (!url) return '#'
    const trimmed = url.trim()
    if (!trimmed) return '#'
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      return trimmed
    }
    return `https://${trimmed}`
  }

  return {
    getWhatsAppUrl,
    normalizeWhatsAppNumber,
    formatWebsiteUrl
  }
}
