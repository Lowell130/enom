export const useOrganic = () => {
  const isOrganicProduct = (product: any): boolean => {
    if (!product) return false

    if (product.custom_attributes && Array.isArray(product.custom_attributes)) {
      const hasOrganicAttr = product.custom_attributes.some((attr: any) => {
        if (!attr || !attr.name || !attr.value) return false
        const name = String(attr.name).toLowerCase().trim()
        const value = String(attr.value).toLowerCase().trim()

        // 1. Attribute name is 'tipo' or 'tipo vino' (or contains 'tipo' without being 'biotipo') and value mentions biologico/bio
        if ((name === 'tipo' || name === 'tipo vino' || (name.includes('tipo') && name !== 'biotipo')) && !name.includes('biolog')) {
          if (/biologic/i.test(value) || /\bbio\b/i.test(value)) return true
        }

        // 2. Attribute name specifically contains 'biolog' or relates to certification/cultivation
        if (name.includes('biolog') || name === 'certificazione' || name === 'coltivazione' || name === 'agricoltura') {
          if (/biologic/i.test(value) || /\bbio\b/i.test(value) || value === 'sì' || value === 'si' || value === 'yes' || value === 'presente') return true
        }

        // 3. Attribute value specifically matches 'vino biologico', 'biologico', 'biologica', or standalone word 'bio'
        if (/^vino biologico$/i.test(value) || /^biologico$/i.test(value) || /^biologica$/i.test(value) || /^\s*bio\s*$/i.test(value)) {
          return true
        }

        return false
      })
      if (hasOrganicAttr) return true
    }

    if (product.is_organic || product.organic) return true

    return false
  }

  return {
    isOrganicProduct
  }
}
