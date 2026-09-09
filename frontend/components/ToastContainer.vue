<template>
  <Teleport to="body">
    <div class="fixed top-5 right-5 z-[999999] flex flex-col space-y-3 max-w-md w-full pointer-events-none px-4 sm:px-0">
      <TransitionGroup
        enter-active-class="transform cubic-bezier(0.34, 1.56, 0.64, 1) duration-300 transition-all"
        enter-from-class="translate-y-[-20px] opacity-0 scale-95"
        enter-to-class="translate-y-0 opacity-100 scale-100"
        leave-active-class="transition-all ease-in duration-200"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-90 translate-x-10"
      >
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="[
            'pointer-events-auto flex items-start space-x-3 p-4 rounded-2xl border shadow-xl backdrop-blur-md transition-all',
            toast.type === 'success' ? 'bg-emerald-900/90 text-white border-emerald-700/80 shadow-emerald-950/20' : '',
            toast.type === 'error' ? 'bg-rose-900/90 text-white border-rose-700/80 shadow-rose-950/20' : '',
            toast.type === 'warning' ? 'bg-amber-900/90 text-white border-amber-700/80 shadow-amber-950/20' : '',
            toast.type === 'info' ? 'bg-stone-900/90 text-white border-stone-700/80 shadow-stone-950/20' : ''
          ]"
        >
          <!-- Icon -->
          <div class="shrink-0 pt-0.5">
            <CheckCircle2 v-if="toast.type === 'success'" class="w-5 h-5 text-emerald-400" />
            <AlertCircle v-else-if="toast.type === 'error'" class="w-5 h-5 text-rose-400" />
            <AlertTriangle v-else-if="toast.type === 'warning'" class="w-5 h-5 text-amber-400" />
            <Info v-else class="w-5 h-5 text-stone-400" />
          </div>

          <!-- Message Body -->
          <div class="flex-1 min-w-0 pr-2">
            <h4 v-if="toast.title" class="text-xs font-bold uppercase tracking-wider mb-0.5 opacity-90">
              {{ toast.title }}
            </h4>
            <p class="text-sm font-medium leading-snug break-words">
              {{ toast.message }}
            </p>
          </div>

          <!-- Close Button -->
          <button
            type="button"
            @click="removeToast(toast.id)"
            class="shrink-0 p-1 rounded-lg opacity-70 hover:opacity-100 hover:bg-white/10 transition-colors"
          >
            <X class="w-4 h-4" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useToast } from '~/composables/useToast'
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-vue-next'

const { toasts, removeToast } = useToast()
</script>
