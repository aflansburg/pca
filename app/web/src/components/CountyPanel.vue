<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchCounties, fetchTracts } from '../api'
import type { County, Tract } from '../types'

const counties = ref<County[]>([])
const tracts = ref<Tract[]>([])
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    ;[counties.value, tracts.value] = await Promise.all([fetchCounties(), fetchTracts()])
  } catch {
    error.value = 'Failed to load access data'
  }
})

// county_name is e.g. "New Castle County"; show just "New Castle".
function shortCounty(name: string | null): string {
  return (name ?? '').replace(/ County.*/, '')
}
</script>

<template>
  <aside class="cpanel">
    <h2>Underserved areas</h2>
    <p v-if="error" class="err">{{ error }}</p>
    <p class="note">
      Underserved = an HRSA-designated Medically Underserved Area (MUA); IMU is the degree (lower =
      worse). Sussex and Kent are whole-county MUAs; New Castle shows its specific designated tracts
      (some New Castle County-Subdivision MUAs are not placed to tracts — a data limitation). Facility
      designations (correctional, FQHC) are listed separately. County counts are individual clinicians
      (organizations excluded).
    </p>

    <h3>Most underserved tracts <span class="note">(worst 15 by IMU)</span></h3>
    <ol class="tracts">
      <li v-for="t in tracts.filter((t) => t.is_underserved).slice(0, 15)" :key="t.tract_fips">
        <span class="imu">IMU {{ t.imu_score ?? '—' }}</span>
        <span class="tf">{{ t.tract_fips }}</span>
        <span class="cn">{{ shortCounty(t.county_name) }}</span>
        <span class="pv">{{ t.pc_provider_count }} PC</span>
      </li>
    </ol>
    <p class="note">
      {{ tracts.filter((t) => t.is_underserved).length }} of {{ tracts.length }} DE tracts are in a
      designated MUA.
    </p>

    <h3>By county <span class="note">(ranked by providers per 10k)</span></h3>
    <div v-for="c in counties" :key="c.county_fips" class="card">
      <div class="ct">
        <strong>{{ shortCounty(c.county_name) }}</strong>
        <span class="badge rate">{{ c.pc_per_10k }} PC / 10k</span>
      </div>
      <div class="stat">
        {{ c.pc_provider_count }} PC providers · {{ c.physician_count }} MD/DO · {{ c.app_provider_count }} NP/PA/CNS
      </div>
      <div class="stat">
        pop {{ c.population.toLocaleString() }} · {{ c.mua_tract_count }} MUA tract(s) ·
        {{ c.mua_designation_count }} MUA designation(s)
      </div>
      <div class="stat">
        area HPSA: {{ c.hpsa_population_count }}<template v-if="c.hpsa_population_max_score">
          · max score {{ c.hpsa_population_max_score }}</template>
      </div>
    </div>

    <h3>Facility designations <span class="note">(separate — not resident access)</span></h3>
    <div v-for="c in counties" :key="'f' + c.county_fips" class="stat">
      {{ shortCounty(c.county_name) }}: {{ c.correctional_hpsa_count }} correctional ·
      {{ c.fqhc_hpsa_count }} FQHC
    </div>
  </aside>
</template>

<style scoped>
.cpanel { padding: 12px; }
h2 { font-size: 14px; margin: 4px 0 8px; }
h3 { font-size: 13px; margin: 14px 0 6px; }
.note { font-size: 11px; color: #666; font-weight: normal; margin: 0 0 8px; }
.card { border: 1px solid #e2e2e2; border-radius: 6px; padding: 8px 10px; margin-bottom: 8px; }
.ct { display: flex; justify-content: space-between; align-items: center; }
.stat { font-size: 12px; color: #333; margin-top: 3px; }
.err { color: #b00; font-size: 12px; }
.badge.rate { background: #2c3e50; color: #fff; padding: 1px 6px; border-radius: 8px; font-size: 11px; }
.tracts { margin: 0 0 4px; padding-left: 20px; }
.tracts li { font-size: 12px; margin-bottom: 3px; display: flex; gap: 6px; align-items: baseline; }
.imu { background: #bd0026; color: #fff; border-radius: 4px; padding: 0 4px; font-size: 11px; }
.tf { color: #333; font-variant-numeric: tabular-nums; }
.cn { color: #666; }
.pv { margin-left: auto; color: #333; }
</style>
