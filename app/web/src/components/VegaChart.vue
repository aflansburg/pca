<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Result } from 'vega-embed'  // type-only; runtime is lazy-loaded below

const props = defineProps<{ specUrl: string }>()
const el = ref<HTMLDivElement | null>(null)
const error = ref<string | null>(null)
let result: Result | null = null

async function render() {
  if (!el.value) return
  error.value = null
  try {
    const res = await fetch(props.specUrl)
    if (!res.ok) throw new Error(String(res.status))
    const spec = await res.json()
    const { default: vegaEmbed } = await import('vega-embed') // code-split: Vega loads only when a chart shows
    result?.finalize()
    result = await vegaEmbed(el.value, spec, { actions: false })
  } catch {
    error.value = 'Failed to load chart'
  }
}

onMounted(render)
watch(() => props.specUrl, render)
onBeforeUnmount(() => result?.finalize())
</script>

<template>
  <div class="vega">
    <div ref="el"></div>
    <p v-if="error" class="err">{{ error }}</p>
  </div>
</template>

<style scoped>
/* Charts use Vega-Lite width:"container"; overflow-x is a backstop if a spec renders fixed-width. */
.vega { width: 100%; overflow-x: auto; }
.err { color: #b00; font-size: 12px; }
</style>
