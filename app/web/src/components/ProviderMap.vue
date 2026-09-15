<script setup lang="ts">
import L from 'leaflet'
import 'leaflet.markercluster'
import { onActivated, onBeforeUnmount, onMounted, ref } from 'vue'

import { fetchCountyGeo, fetchProviders, fetchTractGeo } from '../api'
import type { CountyProps, ProviderProps, TractProps } from '../types'

const el = ref<HTMLDivElement | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
let mapInstance: L.Map | null = null

// Leaflet caches its pixel size; recompute it when the layout changes (resize / rotate / stack).
const onResize = () => mapInstance?.invalidateSize()

const CATEGORY_COLORS: Record<string, string> = {
  Physician: '#1f77b4',
  NP: '#2ca02c',
  PA: '#ff7f0e',
  CNS: '#9467bd',
  Other: '#7f7f7f',
}

function dotIcon(color: string, centroid: boolean): L.DivIcon {
  const cls = centroid ? 'prov-dot centroid' : 'prov-dot'
  return L.divIcon({
    className: '',
    html: `<span class="${cls}" style="--c:${color}"></span>`,
    iconSize: [14, 14],
  })
}

// Underserved tracts (HRSA MUA) are shaded by IMU severity (lower = worse); other tracts
// get only a faint outline for geographic context.
// IMU severity ramp, spread across the DE value clusters (~57-61 severe, ~75-77 mild) so the
// levels read distinctly: maroon (worst) -> red -> orange -> amber (mildest).
function imuColor(imu: number): string {
  if (imu < 59) return '#800026' // e.g. New Castle acute tracts (57.2)
  if (imu < 62) return '#e31a1c' // e.g. Sussex (61.3)
  if (imu < 74) return '#fd8d3c'
  return '#feb24c' // e.g. Kent (75.7), New Castle bulk (77.3)
}

function tractStyle(p: TractProps): L.PathOptions {
  if (!p.is_underserved) return { fillOpacity: 0, color: '#ccc', weight: 0.3 }
  return { fillColor: imuColor(p.imu_score ?? 62), fillOpacity: 0.65, color: '#5a0018', weight: 0.5 }
}

// County overlay: a bold NEUTRAL outline with no fill, so it delineates counties without
// tinting the red tract heat beneath it. Non-interactive so the tract tooltips still work.
function countyStyle(): L.PathOptions {
  return { color: '#1a1a1a', weight: 2.5, fill: false }
}

function popupHtml(p: ProviderProps): string {
  const badges: string[] = []
  if (p.in_mua_tract) badges.push('<span class="badge mua">MUA tract</span>')
  const approx = p.location_source === 'zcta_centroid' ? ' <em>(approx. ZIP centroid)</em>' : ''
  const name = p.provider_name ?? '(organization)'
  return `<strong>${name}</strong><br>${p.provider_category} · ${p.taxonomy_label ?? ''}`
    + `<br>${p.city ?? ''}${approx}<br>${badges.join(' ')}`
}

onMounted(async () => {
  if (!el.value) return
  const map = L.map(el.value).setView([39.15, -75.5], 9) // Delaware
  mapInstance = map
  window.addEventListener('resize', onResize)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19,
  }).addTo(map)

  // Leaflet records a 0/stale size if it mounts before layout settles; recompute once it does.
  requestAnimationFrame(() => map.invalidateSize())
  setTimeout(() => map.invalidateSize(), 200)

  // underserved choropleth, added first so provider markers sit on top of it.
  try {
    const tracts = await fetchTractGeo()
    L.geoJSON<TractProps>(tracts as unknown as GeoJSON.GeoJsonObject, {
      style: (f) => (f ? tractStyle(f.properties) : {}),
      onEachFeature: (f, layer) => {
        const p = f.properties
        if (p.is_underserved) {
          layer.bindTooltip(
            `Tract ${p.tract_fips}<br>IMU ${p.imu_score ?? '—'} · ${p.pc_provider_count} PC providers`,
          )
        }
      },
    }).addTo(map)
  } catch {
    // choropleth is non-critical; providers still render without it
  }

  // County overlay: over tracts, under clusters; non-interactive so tract tooltips still work.
  try {
    const cts = await fetchCountyGeo()
    L.geoJSON<CountyProps>(cts as unknown as GeoJSON.GeoJsonObject, {
      interactive: false,
      style: () => countyStyle(),
    }).addTo(map)
  } catch {
    // county overlay is non-critical
  }

  try {
    const fc = await fetchProviders()
    const cluster = L.markerClusterGroup()
    for (const f of fc.features) {
      const [lon, lat] = f.geometry.coordinates
      const p = f.properties
      const color = CATEGORY_COLORS[p.provider_category] ?? CATEGORY_COLORS.Other
      const marker = L.marker([lat, lon], {
        icon: dotIcon(color, p.location_source === 'zcta_centroid'),
      })
      marker.bindPopup(popupHtml(p))
      cluster.addLayer(marker)
    }
    map.addLayer(cluster)

    const legend = new L.Control({ position: 'bottomright' })
    legend.onAdd = () => {
      const div = L.DomUtil.create('div', 'legend')
      div.innerHTML =
        Object.entries(CATEGORY_COLORS)
          .map(([label, c]) => `<span><i style="background:${c}"></i>${label}</span>`)
          .join('')
        + '<span><i style="background:#800026"></i>more underserved (low IMU)</span>'
        + '<span><i style="background:#feb24c"></i>less underserved</span>'
        + '<span class="note">faded = approx (ZIP centroid)</span>'
      return div
    }
    legend.addTo(map)
  } catch {
    error.value = 'Failed to load providers'
  } finally {
    loading.value = false
  }
})

// Kept alive by <KeepAlive>: the container is display:none while another tab is active, so
// Leaflet's cached size goes stale — recompute when this tab is shown again.
onActivated(() => mapInstance?.invalidateSize())

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  mapInstance?.remove()
  mapInstance = null
})
</script>

<template>
  <div class="mapwrap">
    <div ref="el" class="leaflet"></div>
    <div v-if="loading" class="overlay">Loading providers…</div>
    <div v-if="error" class="overlay err">{{ error }}</div>
  </div>
</template>

<style scoped>
.mapwrap { position: relative; height: 100%; min-height: 0; }
/* Absolute-fill so the map height never depends on a percentage-height chain through the tabs. */
.leaflet { position: absolute; inset: 0; }
.overlay { position: absolute; top: 8px; left: 8px; background: #fff; padding: 4px 8px; border-radius: 4px; z-index: 1000; }
.err { color: #b00; }
</style>
