<template>
  <!-- Copertina illustrata di default: paesaggio diverso per ogni cantina, ricavato dal nome -->
  <svg viewBox="0 0 1200 340" preserveAspectRatio="xMidYMid slice" class="w-full h-full block" aria-hidden="true">
    <defs>
      <linearGradient :id="`${uid}-sky`" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" :stop-color="scene.p.skyTop" />
        <stop offset="0.75" :stop-color="scene.p.skyBottom" />
      </linearGradient>
      <clipPath :id="`${uid}-vines`"><path :d="scene.front" /></clipPath>
    </defs>

    <rect width="1200" height="340" :fill="`url(#${uid}-sky)`" />
    <circle :cx="scene.sun.x" :cy="scene.sun.y" :r="scene.sun.r" :fill="scene.p.sun" opacity="0.7" />
    <circle :cx="scene.sun.x" :cy="scene.sun.y" :r="scene.sun.r * 1.5" :fill="scene.p.sun" opacity="0.16" />
    <g :fill="scene.p.cloud" opacity="0.75">
      <template v-for="(c, i) in scene.clouds" :key="`c${i}`">
        <rect :x="c.x" :y="c.y" :width="c.w" height="8" rx="4" />
        <rect :x="c.x + c.w * 0.25" :y="c.y + 12" :width="c.w * 0.55" height="7" rx="3.5" />
      </template>
    </g>

    <template v-if="scene.coast">
      <rect x="0" :y="scene.coast.y" width="1200" height="200" fill="#A9BDC0" />
      <rect x="0" :y="scene.coast.y" width="1200" height="3" fill="#C9D7D7" />
      <g fill="#DDE7E6" opacity="0.8">
        <rect v-for="(w, i) in scene.coast.waves" :key="`w${i}`" :x="w.x" :y="w.y" :width="w.w" height="2" rx="1" />
      </g>
    </template>
    <path :d="scene.far" :fill="scene.p.far" />
    <path v-for="(cap, i) in scene.snow" :key="`s${i}`" :d="cap" fill="#F4F1EA" opacity="0.85" />
    <path :d="scene.mid" :fill="scene.p.mid" />

    <g v-if="scene.village" :transform="`translate(${scene.village.x} ${scene.village.y}) scale(${scene.village.s})`">
      <rect x="-26" y="-14" width="16" height="14" fill="#EFE3D3" /><path d="M-28 -14 L-18 -21 L-8 -14 Z" :fill="scene.p.roof" />
      <rect x="-10" y="-22" width="12" height="22" fill="#F4EADC" /><path d="M-12 -22 L-4 -28 L4 -22 Z" :fill="scene.p.roof" />
      <rect x="2" y="-40" width="8" height="40" fill="#EADCC9" /><path d="M1 -40 L6 -48 L11 -40 Z" :fill="scene.p.roof" />
      <rect x="10" y="-16" width="20" height="16" fill="#F1E5D5" /><path d="M8 -16 L20 -23 L32 -16 Z" :fill="scene.p.roof" />
      <rect x="30" y="-10" width="12" height="10" fill="#EADCC9" /><path d="M28 -10 L36 -15 L44 -10 Z" :fill="scene.p.roof" />
    </g>

    <g v-if="scene.farm" :transform="`translate(${scene.farm.x} ${scene.farm.y}) scale(${scene.farm.s})`">
      <rect x="-22" y="-16" width="30" height="16" fill="#F1E5D5" /><path d="M-25 -16 L-7 -26 L11 -16 Z" :fill="scene.p.roof" />
      <rect x="8" y="-10" width="18" height="10" fill="#EADCC9" /><path d="M6 -10 L17 -16 L28 -10 Z" :fill="scene.p.roof" />
      <rect x="-15" y="-11" width="4" height="5" fill="#C9B79E" /><rect x="-4" y="-11" width="4" height="5" fill="#C9B79E" />
    </g>
    <path :d="scene.near" :fill="scene.p.near" />
    <g :fill="scene.p.tree">
      <template v-for="(t, i) in scene.trees" :key="`t${i}`">
        <ellipse v-if="scene.cypress" :cx="t.x" :cy="t.y - t.h" rx="6" :ry="t.h" />
        <template v-else>
          <rect :x="t.x - 1.5" :y="t.y - 8" width="3" height="9" />
          <ellipse :cx="t.x" :cy="t.y - 8 - t.h * 0.35" :rx="t.h * 0.6" :ry="t.h * 0.4" opacity="0.85" />
        </template>
      </template>
    </g>

    <path :d="scene.front" :fill="scene.p.front" />
    <g :clip-path="`url(#${uid}-vines)`" stroke-linecap="round">
      <path v-for="(row, i) in scene.rows" :key="`r${i}`" :d="row" :stroke="scene.p.row" stroke-width="7" />
      <path v-for="(row, i) in scene.rows" :key="`l${i}`" :d="row" :stroke="scene.p.leaf" stroke-width="2" stroke-dasharray="3 10" />
    </g>
  </svg>
</template>

<script setup>
import { seededRandom, smoothHill } from '~/utils/wineShapes'

const props = defineProps({
  // di solito il nome della cantina: stesso seme, stessa scena
  seed: { type: String, default: 'EnotecaMolise' },
  // paese della cantina, es. "Campomarino (CB)": sul litorale compare il mare, in provincia di Isernia le montagne
  place: { type: String, default: '' }
})

const COAST_RE = /campomarino|termoli|portocannone|petacciato|montenero di bisaccia|san martino in pensilis|guglionesi|san giacomo degli schiavoni|montecilfone|mafalda|rotello|ururi/i
const MOUNTAIN_RE = /\(is\)|isernia|venafro|agnone|monteroduni|pozzilli|sesto campano|macchia d.isernia|frosolone|capracotta|carovilli|pescolanciano/i

// Tavolozze nei toni del sito: tramonto bordeaux, colline d'oliva, mattino di salvia, sabbia
const PALETTES = [
  { skyTop: '#E8CFC2', skyBottom: '#F5E8DD', sun: '#F1C4AE', cloud: '#FBF3EC', far: '#C3AFAC', mid: '#A88A88', near: '#94696C', front: '#7A4A50', row: '#5E3239', leaf: '#A4766A', tree: '#5E4A44', roof: '#A86E52' },
  { skyTop: '#E4E0CB', skyBottom: '#F3EFE3', sun: '#EFD9A8', cloud: '#FAF7EF', far: '#C3BEA4', mid: '#ADA582', near: '#958D69', front: '#7A7350', row: '#5D5839', leaf: '#A9A27A', tree: '#5E6248', roof: '#B07A5C' },
  { skyTop: '#D7E0D8', skyBottom: '#EEF1EA', sun: '#F3E3C6', cloud: '#F8FAF6', far: '#B4BEB3', mid: '#97A296', near: '#7F8B7E', front: '#647063', row: '#4B5649', leaf: '#97A28F', tree: '#4F5A4C', roof: '#A97458' },
  { skyTop: '#EDD5BE', skyBottom: '#F7EBDD', sun: '#F2C49E', cloud: '#FCF4EA', far: '#D0BDA4', mid: '#B9A083', near: '#A0856A', front: '#846A53', row: '#634E3C', leaf: '#B09378', tree: '#5F4E3F', roof: '#A5694C' },
  { skyTop: '#DED0D8', skyBottom: '#F2EAEC', sun: '#EFC7B8', cloud: '#F9F3F5', far: '#BAB0BB', mid: '#A0949F', near: '#887D88', front: '#6F606C', row: '#50424E', leaf: '#9C8C98', tree: '#4E4650', roof: '#A86E52' },
  { skyTop: '#EFE0BC', skyBottom: '#F8F1DE', sun: '#F3D08F', cloud: '#FCF8EC', far: '#CFC49F', mid: '#BBAB7B', near: '#A39162', front: '#89754A', row: '#6A5734', leaf: '#B9A372', tree: '#5F5838', roof: '#A86E52' }
]

const scene = computed(() => {
  const rnd = seededRandom(props.seed || 'EnotecaMolise')
  const r = (min, max) => min + rnd() * (max - min)
  const p = PALETTES[Math.floor(rnd() * PALETTES.length)]

  const coastal = COAST_RE.test(props.place)
  const mountain = !coastal && MOUNTAIN_RE.test(props.place)

  // monti in lontananza: a punta (Appennino) oppure morbidi; sul litorale colline basse e il mare
  const peaks = mountain || (!coastal && rnd() < 0.45)
  const farPts = []
  for (let x = -60; x <= 1260; x += peaks ? 95 : 160) {
    farPts.push([x, peaks ? r(mountain ? 85 : 105, 170) : coastal ? r(158, 182) : r(140, 175)])
  }
  // sul litorale le colline lontane coprono solo una parte dell'orizzonte: il resto e' mare
  if (coastal) {
    const side = rnd() < 0.5
    farPts.forEach(pt => { if (side ? pt[0] > 560 : pt[0] < 640) pt[1] = 240 })
  }
  let far
  const snow = []
  if (peaks) {
    far = `M${farPts.map(([x, y]) => `${x} ${y.toFixed(1)}`).join(' L')} L1260 340 L-60 340 Z`
    farPts.forEach(([x, y], i) => {
      const prev = farPts[i - 1]
      const next = farPts[i + 1]
      if (prev && next && y < prev[1] - 18 && y < next[1] - 18 && y < 130) {
        snow.push(`M${x} ${y} L${x - 13} ${y + 10} L${x - 5} ${y + 11} L${x + 2} ${y + 6} L${x + 9} ${y + 11} L${x + 14} ${y + 8} Z`)
      }
    })
  } else {
    far = smoothHill(farPts, 340)
  }

  const midPts = []
  for (let x = -100; x <= 1300; x += 200) midPts.push([x, r(178, 214)])
  const nearPts = []
  for (let x = -120; x <= 1320; x += 240) nearPts.push([x, r(212, 240)])
  const frontPts = []
  for (let x = -150; x <= 1350; x += 300) frontPts.push([x, r(250, 272)])

  // borgo sulla cresta della collina intermedia (passa esattamente per i punti di controllo)
  // sulla collina intermedia: borgo, masseria isolata oppure solo campagna
  const vIndex = 2 + Math.floor(rnd() * 3)
  const building = rnd()
  const village = building < 0.5 ? { x: midPts[vIndex][0], y: midPts[vIndex][1] + 3, s: r(1.3, 1.7) } : null
  const fIndex = 1 + Math.floor(rnd() * 4)
  const farm = building >= 0.5 && building < 0.8 ? { x: nearPts[fIndex][0], y: nearPts[fIndex][1] + 3, s: r(1.4, 1.8) } : null
  const cypress = rnd() < 0.55

  const trees = []
  nearPts.slice(1, -1).forEach(([x, y]) => {
    if (rnd() < 0.55) {
      const n = 1 + Math.floor(rnd() * 3)
      for (let k = 0; k < n; k++) trees.push({ x: x + k * 15, y: y + 4, h: r(14, 26) })
    }
  })

  // filari in prospettiva verso un punto di fuga oltre la collina
  const vx = r(380, 820)
  const rows = Array.from({ length: 26 }, (_, i) => {
    const x = -700 + i * 100
    return `M${x} 360 L${(vx + (x - vx) * 0.1).toFixed(1)} 236`
  })

  const coast = coastal
    ? { y: r(150, 162), waves: Array.from({ length: 9 }, () => ({ x: r(0, 1150), y: r(166, 205), w: r(20, 60) })) }
    : null

  const clouds = Array.from({ length: 2 + Math.floor(rnd() * 2) }, () => ({ x: r(40, 1050), y: r(30, 90), w: r(70, 130) }))

  return {
    p,
    sun: { x: r(180, 1020), y: r(70, 115), r: r(30, 46) },
    clouds,
    far,
    snow,
    mid: smoothHill(midPts, 340),
    near: smoothHill(nearPts, 340),
    front: smoothHill(frontPts, 340),
    village,
    farm,
    cypress,
    coast,
    trees,
    rows
  }
})

// id univoci per gradiente e ritaglio (lo stesso seme produce lo stesso disegno)
const uid = computed(() => `cov${Math.floor(seededRandom(props.seed || 'x')() * 1e9).toString(36)}`)
</script>
