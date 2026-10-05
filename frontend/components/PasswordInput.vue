<template>
  <!-- Campo password con il pulsante per mostrarla o nasconderla -->
  <div class="relative">
    <input
      :id="id"
      :value="modelValue"
      :type="visible ? 'text' : 'password'"
      :autocomplete="autocomplete"
      :minlength="minlength || undefined"
      required
      class="input pr-12"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <button
      type="button"
      class="absolute right-1.5 top-1/2 -translate-y-1/2 w-9 h-9 rounded-lg flex items-center justify-center text-ink-mute hover:text-ink hover:bg-sand-100"
      :aria-label="visible ? 'Nascondi la password' : 'Mostra la password'"
      :aria-pressed="visible"
      @click="visible = !visible"
    >
      <EyeOff v-if="visible" class="w-[18px] h-[18px]" aria-hidden="true" />
      <Eye v-else class="w-[18px] h-[18px]" aria-hidden="true" />
    </button>
  </div>
</template>

<script setup>
import { Eye, EyeOff } from 'lucide-vue-next'

defineProps({
  modelValue: { type: String, default: '' },
  id: { type: String, default: undefined },
  autocomplete: { type: String, default: 'current-password' },
  minlength: { type: Number, default: 0 }
})
defineEmits(['update:modelValue'])

const visible = ref(false)
</script>
