<template>
  <!-- Paesaggio molisano illustrato, diverso a ogni visita: colline, mare o Appennino, con una bottiglia in primo piano -->
  <svg viewBox="0 0 500 400" preserveAspectRatio="xMidYMid slice" class="w-full h-full block" role="img" :aria-label="scene.label">
    <defs>
      <linearGradient id="hero-sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" :stop-color="scene.p.skyTop" />
        <stop offset="0.7" :stop-color="scene.p.skyBottom" />
      </linearGradient>
      <clipPath id="hero-vineyard"><path :d="scene.front" /></clipPath>
    </defs>

    <rect width="500" height="400" fill="url(#hero-sky)" />
    <circle :cx="scene.sun.x" :cy="scene.sun.y" :r="scene.sun.r" :fill="scene.p.sun" opacity="0.75" />
    <circle :cx="scene.sun.x" :cy="scene.sun.y" :r="scene.sun.r * 1.45" :fill="scene.p.sun" opacity="0.18" />
    <g :fill="scene.p.cloud" opacity="0.85">
      <template v-for="(c, i) in scene.clouds" :key="`c${i}`">
        <rect :x="c.x" :y="c.y" :width="c.w" height="7" rx="3.5" />
        <rect :x="c.x + c.w * 0.25" :y="c.y + 11" :width="c.w * 0.6" height="6" rx="3" />
      </template>
    </g>

    <!-- orizzonte: mare, colline o Appennino -->
    <template v-if="scene.sea">
      <rect x="0" :y="scene.sea.y" width="500" height="200" fill="#A9BDC0" />
      <rect x="0" :y="scene.sea.y" width="500" height="2.5" fill="#C9D7D7" />
      <g fill="#DDE7E6" opacity="0.85">
        <rect v-for="(w, i) in scene.sea.waves" :key="`w${i}`" :x="w.x" :y="w.y" :width="w.w" height="1.8" rx="0.9" />
      </g>
    </template>
    <path :d="scene.far" :fill="scene.p.far" />
    <path v-for="(cap, i) in scene.snow" :key="`s${i}`" :d="cap" fill="#F4F1EA" opacity="0.9" />

    <path :d="scene.mid" :fill="scene.p.mid" />
    <g v-if="scene.village" :transform="`translate(${scene.village.x} ${scene.village.y}) scale(${scene.village.s})`">
      <rect x="-26" y="-14" width="16" height="14" fill="#EFE3D3" /><path d="M-28 -14 L-18 -21 L-8 -14 Z" :fill="scene.p.roof" />
      <rect x="-10" y="-22" width="12" height="22" fill="#F4EADC" /><path d="M-12 -22 L-4 -28 L4 -22 Z" :fill="scene.p.roof" />
      <rect x="2" y="-40" width="8" height="40" fill="#EADCC9" /><path d="M1 -40 L6 -48 L11 -40 Z" :fill="scene.p.roof" /><rect x="4.5" y="-36" width="3" height="4" rx="1.5" fill="#B9A58C" />
      <rect x="10" y="-16" width="20" height="16" fill="#F1E5D5" /><path d="M8 -16 L20 -23 L32 -16 Z" :fill="scene.p.roof" />
      <rect x="30" y="-10" width="12" height="10" fill="#EADCC9" /><path d="M28 -10 L36 -15 L44 -10 Z" :fill="scene.p.roof" />
      <g fill="#C9B79E"><rect x="-6" y="-16" width="3" height="4" /><rect x="15" y="-11" width="3" height="4" /><rect x="22" y="-11" width="3" height="4" /></g>
    </g>

    <path :d="scene.near" :fill="scene.p.near" />
    <g :fill="scene.p.tree">
      <template v-for="(t, i) in scene.trees" :key="`t${i}`">
        <ellipse v-if="scene.cypress" :cx="t.x" :cy="t.y - t.h" rx="4.5" :ry="t.h" />
        <template v-else>
          <rect :x="t.x - 1.2" :y="t.y - 6" width="2.4" height="7" />
          <ellipse :cx="t.x" :cy="t.y - 6 - t.h * 0.35" :rx="t.h * 0.6" :ry="t.h * 0.4" opacity="0.85" />
        </template>
      </template>
    </g>

    <!-- vigneto con i filari in prospettiva -->
    <path :d="scene.front" :fill="scene.p.front" />
    <g clip-path="url(#hero-vineyard)" stroke-linecap="round">
      <path v-for="(row, i) in scene.rows" :key="`r${i}`" :d="row" :stroke="scene.p.row" stroke-width="5" />
      <path v-for="(row, i) in scene.rows" :key="`l${i}`" :d="row" :stroke="scene.p.leaf" stroke-width="1.4" stroke-dasharray="2 7" />
    </g>

    <!-- piano d'appoggio, bottiglia e calice (a destra o a sinistra) -->
    <g :transform="scene.left ? 'translate(500 0) scale(-1 1)' : undefined">
      <path d="M300 376 C360 368 440 366 500 370 L500 400 L280 400 Z" fill="#EDE5DA" />
      <ellipse cx="404" cy="379" rx="26" ry="4" fill="#3B1D24" opacity="0.15" />
    </g>
    <g :transform="`translate(${scene.left ? 100 : 400} 377) scale(1.55)`">
      <path :d="scene.wine.shape" :fill="scene.wine.bottle" /><path :d="CAPSULE" :fill="scene.wine.capsule" />
      <rect x="-10" y="-46" width="20" height="25" rx="1.5" fill="#F3ECE3" />
      <rect x="-6" y="-39" width="12" height="2" :fill="scene.wine.accent" /><rect x="-4" y="-33" width="8" height="1.3" fill="#B7A79A" /><rect x="-5" y="-29" width="10" height="1.3" fill="#B7A79A" />
      <rect x="-10" y="-60" width="3" height="52" rx="1.5" fill="#fff" :opacity="scene.wine.shine" />
    </g>
    <g :transform="`translate(${scene.left ? 48 : 452} 378) scale(1.45)`">
      <path :d="GLASS" fill="#fff" opacity="0.45" /><path :d="GLASS_WINE" :fill="scene.wine.glass" />
      <rect x="-0.8" y="-40" width="1.6" height="38" fill="#fff" opacity="0.6" /><ellipse cx="0" cy="-1" rx="9" ry="2" fill="#fff" opacity="0.6" />
    </g>
  </svg>
</template>

<script setup>
import { BORDEAUX, BURGUNDY, CAPSULE, GLASS, GLASS_WINE, PALETTES, seededRandom, smoothHill } from '~/utils/wineShapes'

// Seme scelto dal server e riusato nel browser (nessuno "sfarfallio" all'idratazione);
// tornando alla home senza ricaricare la pagina se ne sceglie uno nuovo.
const nuxtApp = useNuxtApp()
const seed = useState('hero-seed', () => Math.random().toString(36).slice(2, 10))
if (import.meta.client && !nuxtApp.isHydrating) seed.value = Math.random().toString(36).slice(2, 10)

const WINES = [
  { name: 'rosso', shape: BORDEAUX, bottle: '#3B1D24', capsule: '#B08A4E', accent: '#8C5A5F', glass: '#5A1F2C', shine: 0.16 },
  { name: 'rosso', shape: BURGUNDY, bottle: '#2F1A1F', capsule: '#7A2335', accent: '#7A2335', glass: '#5A1F2C', shine: 0.16 },
  { name: 'bianco', shape: BURGUNDY, bottle: '#8E9B6A', capsule: '#B08A4E', accent: '#7F8B80', glass: '#E3D58F', shine: 0.3 },
  { name: 'rosato', shape: BORDEAUX, bottle: '#D88A86', capsule: '#F3ECE3', accent: '#B85C62', glass: '#E8A49C', shine: 0.32 }
]
const LANDSCAPES = { colline: 'colline', mare: 'il mare', monti: "l'Appennino" }

const scene = computed(() => {
  const rnd = seededRandom(seed.value)
  const r = (min, max) => min + rnd() * (max - min)
  const p = PALETTES[Math.floor(rnd() * PALETTES.length)]
  const kind = ['colline', 'mare', 'monti'][Math.floor(rnd() * 3)]
  const left = rnd() < 0.5
  const wine = WINES[Math.floor(rnd() * WINES.length)]

  // orizzonte
  const snow = []
  let far
  let sea = null
  if (kind === 'monti') {
    const pts = []
    for (let x = -20; x <= 520; x += 42) pts.push([x, r(128, 200)])
    far = `M${pts.map(([x, y]) => `${x} ${y.toFixed(1)}`).join(' L')} L520 400 L-20 400 Z`
    pts.forEach(([x, y], i) => {
      const prev = pts[i - 1]
      const next = pts[i + 1]
      if (prev && next && y < prev[1] - 14 && y < next[1] - 14 && y < 170) {
        snow.push(`M${x} ${y} L${x - 12} ${y + 10} L${x - 5} ${y + 11} L${x + 2} ${y + 6} L${x + 9} ${y + 11} L${x + 14} ${y + 8} Z`)
      }
    })
  } else {
    const pts = []
    for (let x = -40; x <= 540; x += 90) pts.push([x, kind === 'mare' ? r(196, 214) : r(176, 210)])
    if (kind === 'mare') {
      sea = { y: r(196, 204), waves: Array.from({ length: 8 }, () => ({ x: r(0, 470), y: r(208, 232), w: r(12, 34) })) }
      // le colline lontane coprono solo un lato dell'orizzonte
      pts.forEach(pt => { if (left ? pt[0] < 260 : pt[0] > 240) pt[1] = 260 })
    }
    far = smoothHill(pts, 400)
  }

  const midPts = []
  for (let x = -50; x <= 550; x += 110) midPts.push([x, r(222, 248)])
  const nearPts = []
  for (let x = -60; x <= 560; x += 124) nearPts.push([x, r(250, 268)])
  const frontPts = []
  for (let x = -80; x <= 580; x += 165) frontPts.push([x, r(276, 300)])

  // borgo sul lato opposto alla bottiglia
  const candidates = midPts.filter(([x]) => (left ? x > 260 && x < 470 : x > 30 && x < 240))
  const spot = candidates[Math.floor(rnd() * candidates.length)]
  const village = spot && rnd() < 0.8 ? { x: spot[0], y: spot[1] + 3, s: r(1, 1.25) } : null

  const cypress = rnd() < 0.6
  const trees = []
  nearPts.slice(1, -1).forEach(([x, y]) => {
    if (rnd() < 0.6) {
      const n = 1 + Math.floor(rnd() * 3)
      for (let k = 0; k < n; k++) trees.push({ x: x + k * 11, y: y + 3, h: r(11, 20) })
    }
  })

  const vx = r(150, 350)
  const rows = Array.from({ length: 17 }, (_, i) => {
    const x = -320 + i * 70
    return `M${x} 410 L${(vx + (x - vx) * 0.12).toFixed(1)} 268`
  })

  const clouds = Array.from({ length: 2 + Math.floor(rnd() * 2) }, () => ({ x: r(20, 400), y: r(50, 120), w: r(50, 95) }))

  return {
    p,
    left,
    wine,
    sun: { x: r(70, 430), y: r(95, 165), r: r(32, 46) },
    clouds,
    sea,
    far,
    snow,
    mid: smoothHill(midPts, 400),
    near: smoothHill(nearPts, 400),
    front: smoothHill(frontPts, 400),
    village,
    cypress,
    trees,
    rows,
    label: `Illustrazione di un vigneto molisano con ${LANDSCAPES[kind]} sullo sfondo e una bottiglia di vino ${wine.name}`
  }
})
</script>
