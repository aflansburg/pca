<script setup lang="ts">
import CountyPanel from './CountyPanel.vue'
import ProviderMap from './ProviderMap.vue'
</script>

<template>
  <div class="access">
    <ProviderMap class="map" />
    <CountyPanel class="panel" />
  </div>
</template>

<style scoped>
.access { flex: 1; display: flex; height: 100%; min-width: 0; min-height: 0; }
.map { flex: 1; min-width: 0; min-height: 0; }
.panel { width: 320px; overflow: auto; border-left: 1px solid #ddd; }

/* Mobile (see style.css breakpoint): stack the map above the county panel. */
@media (max-width: 768px) {
  .access { flex-direction: column; }
  .map { flex: none; height: 55vh; min-height: 240px; }
  .panel { width: auto; border-left: none; border-top: 1px solid #ddd; }
}
</style>
