export const useWhatsApp = () => {
  const getWhatsAppUrl = (options: {
    number?: string
    companyName?: string
    productName?: string
  }): string => {
    if (!options.number) return '#'
    const cleanNumber = options.number.replace(/\D/g, '')
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
    formatWebsiteUrl
  }
}
