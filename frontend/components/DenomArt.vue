<template>
  <!-- Illustrazioni delle denominazioni: paesaggio + bottiglie, nei toni del sito -->
  <svg viewBox="0 0 480 140" preserveAspectRatio="xMidYMid slice" class="w-full h-full block" aria-hidden="true">
    <rect width="480" height="140" :fill="scene.sky" />

    <!-- TINTILIA: colline vitate, una bottiglia di rosso e un calice -->
    <template v-if="variant === 'tintilia'">
      <circle cx="372" cy="40" r="16" fill="#E9C9B8" opacity="0.55" />
      <path d="M0 92 C70 70 130 74 200 86 C270 98 330 70 480 78 L480 140 L0 140 Z" fill="#7A4A50" />
      <path d="M0 112 C90 94 170 100 250 108 C330 116 400 98 480 102 L480 140 L0 140 Z" fill="#6A3D44" />
      <g stroke="#8C5A5F" stroke-width="1.6" stroke-linecap="round" opacity="0.8">
        <path v-for="i in 9" :key="`r${i}`" :d="`M${i * 52 - 30} 140 L${i * 40 + 30} 104`" />
      </g>
      <g :transform="`translate(226 128)`"><path :d="BORDEAUX" fill="#3B1D24" /><path :d="CAPSULE_B" fill="#B08A4E" /><rect x="-10" y="-44" width="20" height="22" rx="1.5" fill="#F3ECE3" /><rect x="-6" y="-37" width="12" height="2" fill="#8C5A5F" /><rect x="-4" y="-31" width="8" height="1.4" fill="#B7A79A" /><rect x="-10" y="-60" width="3" height="52" rx="1.5" fill="#fff" opacity="0.14" /></g>
      <g :transform="`translate(262 128)`"><path :d="GLASS" fill="#fff" opacity="0.28" /><path :d="GLASS_WINE" fill="#5A1F2C" /><rect x="-0.8" y="-40" width="1.6" height="38" fill="#fff" opacity="0.4" /><ellipse cx="0" cy="-1" rx="9" ry="2" fill="#fff" opacity="0.4" /></g>
      <g fill="#4F2530" opacity="0.9" transform="translate(186 112)">
        <circle cx="0" cy="0" r="4" /><circle cx="7" cy="0" r="4" /><circle cx="14" cy="0" r="4" /><circle cx="3.5" cy="6" r="4" /><circle cx="10.5" cy="6" r="4" /><circle cx="7" cy="12" r="4" />
        <path d="M7 -4 L9 -11" stroke="#4F2530" stroke-width="1.4" /><path d="M9 -9 C14 -13 19 -10 20 -7 C15 -6 12 -7 9 -9 Z" fill="#6E7A5C" />
      </g>
    </template>

    <!-- BIFERNO: il fiume che scende verso il mare, rosso, rosato e bianco -->
    <template v-else-if="variant === 'biferno'">
      <rect y="70" width="480" height="10" fill="#B9B08F" />
      <path d="M0 78 C60 58 120 62 170 74 C230 88 300 56 380 66 C420 70 450 74 480 72 L480 140 L0 140 Z" fill="#857A57" />
      <path d="M0 104 C80 90 160 96 240 104 C320 112 400 94 480 98 L480 140 L0 140 Z" fill="#766C4C" />
      <path d="M402 70 C370 86 330 92 300 104 C268 117 250 128 236 140 L262 140 C276 128 300 118 330 108 C362 97 392 88 416 72 Z" fill="#C9C1A3" opacity="0.85" />
      <g :transform="`translate(196 128)`"><path :d="BORDEAUX" fill="#3B1D24" /><path :d="CAPSULE_B" fill="#7A2335" /><rect x="-10" y="-44" width="20" height="20" rx="1.5" fill="#F3ECE3" /><rect x="-6" y="-37" width="12" height="2" fill="#7A2335" /><rect x="-10" y="-60" width="3" height="52" rx="1.5" fill="#fff" opacity="0.14" /></g>
      <g :transform="`translate(240 132) scale(0.94)`"><path :d="BORDEAUX" fill="#D88A86" /><path :d="CAPSULE_B" fill="#F3ECE3" /><rect x="-10" y="-44" width="20" height="20" rx="1.5" fill="#F3ECE3" /><rect x="-6" y="-37" width="12" height="2" fill="#B85C62" /><rect x="-10" y="-60" width="3" height="52" rx="1.5" fill="#fff" opacity="0.3" /></g>
      <g :transform="`translate(284 128)`"><path :d="BORDEAUX" fill="#D9CC8A" /><path :d="CAPSULE_B" fill="#B08A4E" /><rect x="-10" y="-44" width="20" height="20" rx="1.5" fill="#F3ECE3" /><rect x="-6" y="-37" width="12" height="2" fill="#9A8F6C" /><rect x="-10" y="-60" width="3" height="52" rx="1.5" fill="#fff" opacity="0.35" /></g>
    </template>

    <!-- PENTRO: le cime dell'Appennino, borgognotta e calice di bianco -->
    <template v-else>
      <path d="M0 96 L60 52 L96 74 L150 30 L206 80 L250 56 L300 92 L360 40 L420 78 L480 58 L480 140 L0 140 Z" fill="#6E7A70" />
      <path d="M150 30 L136 41 L144 43 L152 38 L160 44 L166 40 Z M360 40 L347 50 L355 52 L362 47 L370 52 L374 49 Z M60 52 L50 59 L57 60 L63 56 L68 58 Z" fill="#E9EDE6" opacity="0.85" />
      <path d="M0 108 C90 96 170 100 250 110 C330 120 410 100 480 104 L480 140 L0 140 Z" fill="#5E695F" />
      <g :transform="`translate(226 128)`"><path :d="BURGUNDY" fill="#2F3A30" /><path :d="CAPSULE_G" fill="#B08A4E" /><rect x="-11" y="-40" width="22" height="20" rx="1.5" fill="#F3ECE3" /><rect x="-7" y="-33" width="14" height="2" fill="#7F8B80" /><rect x="-4" y="-27" width="8" height="1.4" fill="#B7A79A" /><rect x="-11" y="-50" width="3" height="44" rx="1.5" fill="#fff" opacity="0.14" /></g>
      <g :transform="`translate(262 128)`"><path :d="GLASS" fill="#fff" opacity="0.3" /><path :d="GLASS_WINE" fill="#E3D58F" opacity="0.95" /><rect x="-0.8" y="-40" width="1.6" height="38" fill="#fff" opacity="0.45" /><ellipse cx="0" cy="-1" rx="9" ry="2" fill="#fff" opacity="0.45" /></g>
    </template>
  </svg>
</template>

<script setup>
const props = defineProps({
  // 'tintilia' | 'biferno' | 'pentro'
  variant: { type: String, default: 'tintilia' }
})

// Sagome disegnate con la base in (0, 0) e altezza 100
const BORDEAUX = 'M-13 0 L-13 -60 C-13 -68 -4.5 -70 -4.5 -77 L-4.5 -94 L-5.5 -95 L-5.5 -100 L5.5 -100 L5.5 -95 L4.5 -94 L4.5 -77 C4.5 -70 13 -68 13 -60 L13 0 Q13 2 11 2 L-11 2 Q-13 2 -13 0 Z'
const CAPSULE_B = 'M-4.5 -86 L-4.5 -94 L-5.5 -95 L-5.5 -100 L5.5 -100 L5.5 -95 L4.5 -94 L4.5 -86 Z'
const BURGUNDY = 'M-14 0 L-14 -46 C-14 -64 -4.5 -68 -4.5 -80 L-4.5 -94 L-5.5 -95 L-5.5 -100 L5.5 -100 L5.5 -95 L4.5 -94 L4.5 -80 C4.5 -68 14 -64 14 -46 L14 0 Q14 2 12 2 L-12 2 Q-14 2 -14 0 Z'
const CAPSULE_G = 'M-4.5 -86 L-4.5 -94 L-5.5 -95 L-5.5 -100 L5.5 -100 L5.5 -95 L4.5 -94 L4.5 -86 Z'
const GLASS = 'M-12 -66 L12 -66 C12 -50 7 -42 0 -41 C-7 -42 -12 -50 -12 -66 Z'
const GLASS_WINE = 'M-11.3 -55 L11.3 -55 C10.5 -47 6 -42.5 0 -42 C-6 -42.5 -10.5 -47 -11.3 -55 Z'

const SCENES = {
  tintilia: { sky: '#8C5A5F' },
  biferno: { sky: '#9A8F6C' },
  pentro: { sky: '#7F8B80' }
}
const scene = computed(() => SCENES[props.variant] || SCENES.tintilia)
</script>
