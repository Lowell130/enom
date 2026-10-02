<template>
  <!-- Paesaggio molisano illustrato: Appennino, borgo in collina, vigneto e una bottiglia in primo piano -->
  <svg viewBox="0 0 500 400" preserveAspectRatio="xMidYMid slice" class="w-full h-full block" role="img" aria-label="Illustrazione di un vigneto molisano al tramonto, con un borgo in collina e una bottiglia di vino">
    <defs>
      <linearGradient id="hero-sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#EBD3C3" />
        <stop offset="0.65" stop-color="#F5E7DA" />
      </linearGradient>
      <clipPath id="hero-vineyard"><path :d="vineyard" /></clipPath>
    </defs>

    <rect width="500" height="400" fill="url(#hero-sky)" />
    <circle cx="352" cy="148" r="44" fill="#F1C9AE" opacity="0.75" />
    <circle cx="352" cy="148" r="64" fill="#F1C9AE" opacity="0.18" />
    <!-- nuvole leggere -->
    <g fill="#FBF4EC" opacity="0.8">
      <rect x="60" y="88" width="90" height="7" rx="3.5" /><rect x="84" y="99" width="56" height="6" rx="3" />
      <rect x="248" y="62" width="70" height="6" rx="3" />
    </g>

    <!-- Appennino -->
    <path d="M0 214 L36 192 L70 200 L118 160 L150 182 L196 170 L236 186 L292 146 L330 172 L366 164 L410 184 L456 166 L500 180 L500 400 L0 400 Z" fill="#BCC2B5" />
    <path d="M118 160 L106 170 L113 171 L120 166 L127 171 L132 168 Z M292 146 L280 156 L287 157 L294 152 L301 157 L306 154 Z" fill="#F4F1EA" opacity="0.9" />
    <path d="M0 232 C60 214 120 216 180 226 C240 236 300 208 380 214 C430 218 470 224 500 220 L500 400 L0 400 Z" fill="#A5AB98" />

    <!-- collina del borgo -->
    <path d="M0 262 C50 240 110 222 170 228 C230 234 270 252 330 248 C400 243 450 236 500 244 L500 400 L0 400 Z" fill="#A99E7C" />
    <g transform="translate(138 230)">
      <rect x="-26" y="-14" width="16" height="14" fill="#EFE3D3" /><path d="M-28 -14 L-18 -21 L-8 -14 Z" fill="#B47A5C" />
      <rect x="-10" y="-22" width="12" height="22" fill="#F4EADC" /><path d="M-12 -22 L-4 -28 L4 -22 Z" fill="#A86E52" />
      <rect x="2" y="-40" width="8" height="40" fill="#EADCC9" /><path d="M1 -40 L6 -48 L11 -40 Z" fill="#9C6449" /><rect x="4.5" y="-36" width="3" height="4" rx="1.5" fill="#B9A58C" />
      <rect x="10" y="-16" width="20" height="16" fill="#F1E5D5" /><path d="M8 -16 L20 -23 L32 -16 Z" fill="#B47A5C" />
      <rect x="30" y="-10" width="12" height="10" fill="#EADCC9" /><path d="M28 -10 L36 -15 L44 -10 Z" fill="#A86E52" />
      <g fill="#C9B79E"><rect x="-6" y="-16" width="3" height="4" /><rect x="15" y="-11" width="3" height="4" /><rect x="22" y="-11" width="3" height="4" /></g>
    </g>
    <!-- cipressi -->
    <g fill="#6F7560">
      <ellipse cx="232" cy="222" rx="5" ry="20" /><ellipse cx="244" cy="226" rx="4" ry="15" />
      <ellipse cx="404" cy="226" rx="4.5" ry="17" /><ellipse cx="60" cy="236" rx="4" ry="14" />
    </g>

    <!-- vigneto in primo piano con i filari in prospettiva -->
    <path :d="vineyard" fill="#8C5A5F" />
    <g clip-path="url(#hero-vineyard)" stroke-linecap="round">
      <path v-for="row in rows" :key="row" :d="row" stroke="#6A3D44" stroke-width="5" />
      <path v-for="row in rows" :key="`l${row}`" :d="row" stroke="#9E6E62" stroke-width="1.4" stroke-dasharray="2 7" />
    </g>

    <!-- piano d'appoggio, bottiglia e calice -->
    <path d="M300 376 C360 368 440 366 500 370 L500 400 L280 400 Z" fill="#EDE5DA" />
    <ellipse cx="404" cy="379" rx="26" ry="4" fill="#6A3D44" opacity="0.18" />
    <g transform="translate(400 377) scale(1.55)">
      <path :d="BORDEAUX" fill="#3B1D24" /><path :d="CAPSULE" fill="#B08A4E" />
      <rect x="-10" y="-46" width="20" height="25" rx="1.5" fill="#F3ECE3" />
      <rect x="-6" y="-39" width="12" height="2" fill="#8C5A5F" /><rect x="-4" y="-33" width="8" height="1.3" fill="#B7A79A" /><rect x="-5" y="-29" width="10" height="1.3" fill="#B7A79A" />
      <rect x="-10" y="-60" width="3" height="52" rx="1.5" fill="#fff" opacity="0.16" />
    </g>
    <g transform="translate(452 378) scale(1.45)">
      <path :d="GLASS" fill="#fff" opacity="0.45" /><path :d="GLASS_WINE" fill="#5A1F2C" />
      <rect x="-0.8" y="-40" width="1.6" height="38" fill="#fff" opacity="0.6" /><ellipse cx="0" cy="-1" rx="9" ry="2" fill="#fff" opacity="0.6" />
    </g>
  </svg>
</template>

<script setup>
import { BORDEAUX, CAPSULE, GLASS, GLASS_WINE } from '~/utils/wineShapes'

const vineyard = 'M0 300 C90 270 190 266 290 278 C380 289 440 284 500 276 L500 400 L0 400 Z'
// filari che convergono verso un punto di fuga oltre la collina
const rows = Array.from({ length: 15 }, (_, i) => {
  const x = -260 + i * 70
  return `M${x} 410 L${170 + (x - 170) * 0.12} 262`
})
</script>
