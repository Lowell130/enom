<template>
  <!-- Testo semplice formattato: "## " titolo, "- " elenco, riga vuota = nuovo paragrafo.
       Nessun HTML dal database: tutto passa dai nodi di Vue, quindi niente rischi di script. -->
  <div class="flex flex-col gap-4 text-[16px] leading-relaxed text-ink-soft">
    <template v-for="(block, i) in blocks" :key="i">
      <h2 v-if="block.type === 'h'" class="font-serif text-[26px] font-semibold text-ink leading-tight mt-4">{{ block.text }}</h2>
      <ul v-else-if="block.type === 'ul'" class="list-disc pl-6 flex flex-col gap-1.5 m-0">
        <li v-for="(item, j) in block.items" :key="j">{{ item }}</li>
      </ul>
      <p v-else class="m-0 whitespace-pre-line">{{ block.text }}</p>
    </template>
  </div>
</template>

<script setup>
const props = defineProps({ text: { type: String, default: '' } })

const blocks = computed(() => {
  const out = []
  for (const raw of String(props.text || '').split(/\n\s*\n/)) {
    const lines = raw.split('\n').map(l => l.trimEnd()).filter(l => l.trim())
    if (!lines.length) continue
    if (lines.length === 1 && lines[0].startsWith('## ')) {
      out.push({ type: 'h', text: lines[0].slice(3).trim() })
      continue
    }
    // un titolo seguito da righe nello stesso blocco
    if (lines[0].startsWith('## ')) {
      out.push({ type: 'h', text: lines.shift().slice(3).trim() })
    }
    if (lines.every(l => l.trim().startsWith('- '))) {
      out.push({ type: 'ul', items: lines.map(l => l.trim().slice(2)) })
    } else {
      out.push({ type: 'p', text: lines.join('\n') })
    }
  }
  return out
})
</script>
