// Formati comuni ai grafici dell'Osservatorio

const CATEGORY_PLURAL: Record<string, string> = {
  VINO_ROSSO: 'Rossi',
  VINO_BIANCO: 'Bianchi',
  ROSATO: 'Rosati',
  SPUMANTE: 'Spumanti',
  PASSITO: 'Passiti e dolci',
  LIQUORE: 'Liquori e grappe',
  ALTRO: 'Altre tipologie'
}

export const categoryPlural = (cat?: string) => CATEGORY_PLURAL[String(cat || '').toUpperCase()] || cat || ''

// 13.4 -> "13,4"; 14.0 -> "14" (al massimo `decimals` decimali, senza zeri inutili)
export const fmtNumber = (n: number | null | undefined, decimals = 0) => {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return '–'
  return Number(n).toLocaleString('it-IT', { minimumFractionDigits: 0, maximumFractionDigits: decimals })
}

// 20 -> "20 €"; 9.5 -> "9,50 €"
export const fmtEuro = (n: number | null | undefined) => {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return '–'
  const decimals = Number.isInteger(Number(n)) ? 0 : 2
  return `${Number(n).toLocaleString('it-IT', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })} €`
}

export const winesLabel = (n: number) => `${n} ${n === 1 ? 'vino' : 'vini'}`
