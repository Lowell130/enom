// Vitigni nel formato unico del catalogo: "Tintilia 80%", dal vitigno principale al minore.
// Il vitigno principale (percentuale piu' alta) e' la "tipologia" del vino per filtri e card.

export const cleanGrape = (g: unknown) =>
  String(g ?? '').replace(/\s*\d+([.,]\d+)?\s*%/g, '').replace(/\s+/g, ' ').trim()

export const grapePercent = (g: unknown): number | null => {
  const m = String(g ?? '').match(/(\d+(?:[.,]\d+)?)\s*%/)
  return m ? Math.trunc(parseFloat(m[1].replace(',', '.'))) : null
}

/** Nomi dei vitigni dal principale al minore (senza percentuali, senza doppioni). */
export const grapeNames = (product: any): string[] => {
  const list = (product?.grape_varieties || [])
    .map((g: unknown, i: number) => ({ name: cleanGrape(g), pct: grapePercent(g), i }))
    .filter((x: any) => x.name)
    .sort((a: any, b: any) => (a.pct === null ? 1 : 0) - (b.pct === null ? 1 : 0) || (b.pct ?? 0) - (a.pct ?? 0) || a.i - b.i)
  const seen = new Set<string>()
  return list.map((x: any) => x.name).filter((n: string) => !seen.has(n.toLowerCase()) && seen.add(n.toLowerCase()))
}

export const primaryGrape = (product: any): string => grapeNames(product)[0] || ''

/** Come mostrare i vitigni sul sito: un solo vitigno senza percentuale ("Tintilia"), un uvaggio con le
 *  percentuali ("Montepulciano 85%, Aglianico 15%"), sempre dal principale. */
export const grapesLabel = (product: any): string => {
  const list = (product?.grape_varieties || []).filter((g: unknown) => cleanGrape(g))
  if (list.length <= 1) return list.map(cleanGrape).join('')
  const names = grapeNames(product)
  const pct = new Map(list.map((g: unknown) => [cleanGrape(g).toLowerCase(), grapePercent(g)]))
  return names.map(n => (pct.get(n.toLowerCase()) != null ? `${n} ${pct.get(n.toLowerCase())}%` : n)).join(', ')
}
