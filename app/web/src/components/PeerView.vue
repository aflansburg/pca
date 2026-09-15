<script setup lang="ts">
import { ref } from 'vue'

import { fetchPeers, searchProviders } from '../api'
import type { PeerComparison, SearchHit } from '../types'
import VegaChart from './VegaChart.vue'

const q = ref('')
const hits = ref<SearchHit[]>([])
const peer = ref<PeerComparison | null>(null)
const err = ref<string | null>(null)
let timer: number | undefined

function onInput() {
  clearTimeout(timer)
  timer = window.setTimeout(async () => {
    hits.value = q.value.trim().length >= 2 ? await searchProviders(q.value.trim()) : []
  }, 250)
}
async function pick(h: SearchHit) {
  q.value = h.provider_name ?? ''
  hits.value = []
  err.value = null
  try {
    peer.value = await fetchPeers(h.npi)
  } catch {
    peer.value = null
    err.value = 'No peer comparison available for this provider.'
  }
}
</script>

<template>
  <div class="view">
    <h2>Peer comparison</h2>
    <div class="search">
      <input v-model="q" @input="onInput" placeholder="Search a provider with Medicare billing…" />
      <ul v-if="hits.length" class="hits">
        <li v-for="h in hits" :key="h.npi" @click="pick(h)">
          {{ h.provider_name }} <small>{{ h.taxonomy_label }} · {{ h.city }}</small>
        </li>
      </ul>
    </div>
    <p v-if="err" class="warn">{{ err }}</p>
    <template v-if="peer">
      <VegaChart :spec-url="`/api/charts/peers?npi=${peer.npi}`" />
      <p v-if="peer.low_confidence" class="warn">
        Small peer group (n={{ peer.peer_group_size }}) — interpret with caution.
      </p>
      <p class="note">Percentile within {{ peer.taxonomy_label }} peers (n={{ peer.peer_group_size }}).</p>
    </template>
    <p v-else class="note">
      Search and select a provider to compare against same-specialty peers. Only providers with
      Medicare billing appear (the peer data source).
    </p>
  </div>
</template>
