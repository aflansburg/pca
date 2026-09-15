<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchSpending } from '../api'
import type { Spending } from '../types'
import VegaChart from './VegaChart.vue'

const rows = ref<Spending[]>([])
onMounted(async () => {
  rows.value = await fetchSpending()
})

function money(n: number | null): string {
  return n == null ? '—' : '$' + Math.round(n).toLocaleString()
}
</script>

<template>
  <div class="view">
    <h2>Spending by provider type</h2>
    <VegaChart spec-url="/api/charts/spending" />
    <div class="scroll-x" role="region" aria-label="Spending by provider type" tabindex="0">
    <table class="tbl">
      <thead>
        <tr><th>Type</th><th>Providers</th><th>Total paid</th><th>Medical</th><th>Drug</th><th>% of paid</th></tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.provider_category">
          <td>{{ r.provider_category }}</td>
          <td>{{ r.provider_count }}</td>
          <td>{{ money(r.total_medicare_paid) }}</td>
          <td>{{ money(r.medical_paid) }}</td>
          <td>{{ money(r.drug_paid) }}</td>
          <td>{{ r.pct_of_paid }}%</td>
        </tr>
      </tbody>
    </table>
    </div>
  </div>
</template>
