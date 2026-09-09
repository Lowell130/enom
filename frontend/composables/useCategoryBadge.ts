export const useCategoryBadge = () => {
  const categoryMap: Record<string, string> = {
    'VINO_ROSSO': 'Vino Rosso',
    'VINO_BIANCO': 'Vino Bianco',
    'ROSATO': 'Rosato',
    'SPUMANTE': 'Spumante',
    'PASSITO': 'Passito',
    'LIQUORE': 'Liquore / Grappa'
  }

  const badgeClassMap: Record<string, string> = {
    'VINO_ROSSO': 'bg-rose-50 text-rose-900 border-rose-200/90',
    'ROSATO': 'bg-pink-50 text-pink-900 border-pink-200/90',
    'VINO_BIANCO': 'bg-amber-50 text-amber-900 border-amber-200/90',
    'SPUMANTE': 'bg-emerald-50 text-emerald-900 border-emerald-200/90',
    'PASSITO': 'bg-orange-50 text-orange-950 border-orange-200/90',
    'LIQUORE': 'bg-purple-50 text-purple-950 border-purple-200/90'
  }

  const normalizeCategory = (cat?: string): string => {
    if (!cat) return ''
    const upper = cat.trim().toUpperCase().replace(/\s+/g, '_')
    if (badgeClassMap[upper]) return upper
    
    if (upper.includes('ROSSO')) return 'VINO_ROSSO'
    if (upper.includes('ROSATO')) return 'ROSATO'
    if (upper.includes('BIANCO')) return 'VINO_BIANCO'
    if (upper.includes('SPUMANTE')) return 'SPUMANTE'
    if (upper.includes('PASSITO')) return 'PASSITO'
    if (upper.includes('LIQUORE') || upper.includes('GRAPPA')) return 'LIQUORE'
    
    return upper
  }

  const formatCategory = (cat?: string): string => {
    if (!cat) return 'N/D'
    const key = normalizeCategory(cat)
    return categoryMap[key] || cat
  }

  const getCategoryBadgeClass = (cat?: string): string => {
    const key = normalizeCategory(cat)
    return badgeClassMap[key] || 'bg-stone-50 text-stone-700 border-stone-200/80'
  }

  return {
    formatCategory,
    getCategoryBadgeClass
  }
}
