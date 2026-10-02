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
