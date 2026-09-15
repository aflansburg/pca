<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'

import { fetchProviderServices, fetchVolume } from '../api'
import type { ServiceRow, VolumeMetric, VolumeProvider } from '../types'

const detailEl = ref<HTMLElement | null>(null)

const METRICS: { key: VolumeMetric; label: string }[] = [
  { key: 'medical_medicare_paid', label: 'Medical paid' },
  { key: 'total_services', label: 'Services' },
  { key: 'total_beneficiaries', label: 'Beneficiaries' },
]

const metric = ref<VolumeMetric>('medical_medicare_paid')
const rows = ref<VolumeProvider[]>([])
const selected = ref<VolumeProvider | null>(null)
const services = ref<ServiceRow[]>([])

async function load() {
  rows.value = await fetchVolume(metric.value, 50)
}
async function pick(p: VolumeProvider) {
  selected.value = p
  services.value = await fetchProviderServices(p.npi)
  // Mobile: bring the detail (below the list) into view.
  await nextTick()
  detailEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(load)
watch(metric, () => {
  selected.value = null
  load()
})

function metricValue(p: VolumeProvider): string {
  const v = p[metric.value] ?? 0
  return metric.value === 'medical_medicare_paid'
    ? '$' + Math.round(v).toLocaleString()
    : v.toLocaleString()
}
function money(n: number | null): string {
  return n == null ? '—' : '$' + Math.round(n).toLocaleString()
}
function pct(part: number | null, whole: number | null): number {
  if (!whole || part == null) return 0
  return Math.round((part / whole) * 100)
}
</script>

<template>
  <div class="view split">
    <div class="col">
      <h2>Highest-volume providers</h2>
      <div class="toggle">
        <button v-for="m in METRICS" :key="m.key" :class="{ on: metric === m.key }" @click="metric = m.key">
          {{ m.label }}
        </button>
      </div>
      <div class="scroll-x" role="region" aria-label="Highest-volume providers" tabindex="0">
        <table class="tbl">
          <thead>
            <tr><th>Provider</th><th>Type</th><th>{{ METRICS.find((m) => m.key === metric)?.label }}</th></tr>
          </thead>
          <tbody>
            <tr v-for="p in rows" :key="p.npi" :class="{ sel: selected?.npi === p.npi }" @click="pick(p)">
              <td>{{ p.provider_name }}<br /><small>{{ p.taxonomy_label }} · {{ p.city }}</small></td>
              <td>{{ p.provider_category }}</td>
              <td>{{ metricValue(p) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="col" ref="detailEl">
      <h3 v-if="selected">{{ selected.provider_name }} — top services</h3>
      <p v-else class="note">Select a provider to see what they bill for.</p>
      <div v-if="selected" class="split-summary">
        <div class="splitbar" :title="pct(selected.drug_medicare_paid, selected.total_medicare_paid) + '% drug'">
          <span class="seg medical" :style="{ width: pct(selected.medical_medicare_paid, selected.total_medicare_paid) + '%' }"></span>
          <span class="seg drug" :style="{ width: pct(selected.drug_medicare_paid, selected.total_medicare_paid) + '%' }"></span>
        </div>
        <p class="note">
          {{ money(selected.total_medicare_paid) }} paid ·
          {{ money(selected.medical_medicare_paid) }} medical ·
          {{ money(selected.drug_medicare_paid) }} drug
          (<strong>{{ pct(selected.drug_medicare_paid, selected.total_medicare_paid) }}% drug pass-through</strong>)
        </p>
      </div>
      <div v-if="selected" class="scroll-x" role="region" aria-label="Provider services" tabindex="0">
        <table class="tbl">
          <thead><tr><th>HCPCS</th><th>Service</th><th>Services</th><th>Paid</th></tr></thead>
          <tbody>
            <tr v-for="s in services" :key="s.hcpcs_cd + s.place_of_srvc"
                :class="{ drugrow: s.hcpcs_drug_ind === 'Y' }">
              <td>
                {{ s.hcpcs_cd }}
                <span v-if="s.hcpcs_drug_ind === 'Y'" class="tag drug">Drug</span>
              </td>
              <td>{{ s.hcpcs_desc }}</td>
              <td>{{ s.services }}</td>
              <td>{{ money(s.total_medicare_paid) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
