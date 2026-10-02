// Sagome delle illustrazioni (bottiglie e calice): base in (0, 0), altezza 100
export const BORDEAUX = 'M-13 0 L-13 -60 C-13 -68 -4.5 -70 -4.5 -77 L-4.5 -94 L-5.5 -95 L-5.5 -100 L5.5 -100 L5.5 -95 L4.5 -94 L4.5 -77 C4.5 -70 13 -68 13 -60 L13 0 Q13 2 11 2 L-11 2 Q-13 2 -13 0 Z'
export const BURGUNDY = 'M-14 0 L-14 -46 C-14 -64 -4.5 -68 -4.5 -80 L-4.5 -94 L-5.5 -95 L-5.5 -100 L5.5 -100 L5.5 -95 L4.5 -94 L4.5 -80 C4.5 -68 14 -64 14 -46 L14 0 Q14 2 12 2 L-12 2 Q-14 2 -14 0 Z'
export const CAPSULE = 'M-4.5 -86 L-4.5 -94 L-5.5 -95 L-5.5 -100 L5.5 -100 L5.5 -95 L4.5 -94 L4.5 -86 Z'
export const GLASS = 'M-12 -66 L12 -66 C12 -50 7 -42 0 -41 C-7 -42 -12 -50 -12 -66 Z'
export const GLASS_WINE = 'M-11.3 -55 L11.3 -55 C10.5 -47 6 -42.5 0 -42 C-6 -42.5 -10.5 -47 -11.3 -55 Z'

// Generatore pseudo-casuale con seme: lo stesso nome produce sempre la stessa scena
export const seededRandom = (seed: string) => {
  let h = 2166136261
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return () => {
    h += 0x6D2B79F5
    let t = h
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// Curva morbida che passa per tutti i punti (Catmull-Rom convertita in Bézier), chiusa verso il basso
export const smoothHill = (points: [number, number][], bottom: number) => {
  const p = points
  let d = `M${p[0][0]} ${p[0][1]}`
  for (let i = 0; i < p.length - 1; i++) {
    const p0 = p[i - 1] || p[i]
    const p1 = p[i]
    const p2 = p[i + 1]
    const p3 = p[i + 2] || p2
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6]
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6]
    d += ` C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`
  }
  const last = p[p.length - 1]
  return `${d} L${last[0]} ${bottom} L${p[0][0]} ${bottom} Z`
}

// Tavolozze nei toni del sito: tramonto bordeaux, colline d'oliva, mattino di salvia, sabbia, lavanda, oro
export const PALETTES = [
  { skyTop: '#E8CFC2', skyBottom: '#F5E8DD', sun: '#F1C4AE', cloud: '#FBF3EC', far: '#C3AFAC', mid: '#A88A88', near: '#94696C', front: '#7A4A50', row: '#5E3239', leaf: '#A4766A', tree: '#5E4A44', roof: '#A86E52' },
  { skyTop: '#E4E0CB', skyBottom: '#F3EFE3', sun: '#EFD9A8', cloud: '#FAF7EF', far: '#C3BEA4', mid: '#ADA582', near: '#958D69', front: '#7A7350', row: '#5D5839', leaf: '#A9A27A', tree: '#5E6248', roof: '#B07A5C' },
  { skyTop: '#D7E0D8', skyBottom: '#EEF1EA', sun: '#F3E3C6', cloud: '#F8FAF6', far: '#B4BEB3', mid: '#97A296', near: '#7F8B7E', front: '#647063', row: '#4B5649', leaf: '#97A28F', tree: '#4F5A4C', roof: '#A97458' },
  { skyTop: '#EDD5BE', skyBottom: '#F7EBDD', sun: '#F2C49E', cloud: '#FCF4EA', far: '#D0BDA4', mid: '#B9A083', near: '#A0856A', front: '#846A53', row: '#634E3C', leaf: '#B09378', tree: '#5F4E3F', roof: '#A5694C' },
  { skyTop: '#DED0D8', skyBottom: '#F2EAEC', sun: '#EFC7B8', cloud: '#F9F3F5', far: '#BAB0BB', mid: '#A0949F', near: '#887D88', front: '#6F606C', row: '#50424E', leaf: '#9C8C98', tree: '#4E4650', roof: '#A86E52' },
  { skyTop: '#EFE0BC', skyBottom: '#F8F1DE', sun: '#F3D08F', cloud: '#FCF8EC', far: '#CFC49F', mid: '#BBAB7B', near: '#A39162', front: '#89754A', row: '#6A5734', leaf: '#B9A372', tree: '#5F5838', roof: '#A86E52' }
]
