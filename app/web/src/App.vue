<script setup lang="ts">
import { computed, ref } from 'vue'

import AccessView from './components/AccessView.vue'
import GroupsView from './components/GroupsView.vue'
import PeerView from './components/PeerView.vue'
import SpendingView from './components/SpendingView.vue'
import VolumeView from './components/VolumeView.vue'

const tabs = [
  { key: 'access', label: 'Access (map)', component: AccessView },
  { key: 'volume', label: 'Volume', component: VolumeView },
  { key: 'spending', label: 'Spending', component: SpendingView },
  { key: 'groups', label: 'Practice groups', component: GroupsView },
  { key: 'peers', label: 'Peer compare', component: PeerView },
]

const active = ref('access')
const currentComponent = computed(
  () => tabs.find((t) => t.key === active.value)?.component ?? AccessView,
)

// Select a tab and keep the clicked one visible in the horizontally-scrolling bar (mobile).
function selectTab(key: string, event: MouseEvent) {
  active.value = key
  ;(event.currentTarget as HTMLElement).scrollIntoView({ inline: 'nearest', block: 'nearest', behavior: 'smooth' })
}
</script>

<template>
  <div class="layout">
    <header>
      <h1>Primary Care Atlas — Delaware</h1>
      <nav class="tabs">
        <button v-for="t in tabs" :key="t.key" :class="{ on: active === t.key }" @click="selectTab(t.key, $event)">
          {{ t.label }}
        </button>
      </nav>
    </header>
    <div class="body">
      <!-- KeepAlive so switching tabs doesn't remount/refetch (the map holds 4,508 providers). -->
      <KeepAlive>
        <component :is="currentComponent" />
      </KeepAlive>
    </div>
  </div>
</template>
