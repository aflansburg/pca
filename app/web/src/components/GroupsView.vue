<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'

import { fetchGroupMembers, fetchGroups } from '../api'
import type { Group, Member } from '../types'

const groups = ref<Group[]>([])
const selected = ref<Group | null>(null)
const members = ref<Member[]>([])
const detailEl = ref<HTMLElement | null>(null)

onMounted(async () => {
  groups.value = await fetchGroups()
})
async function pick(g: Group) {
  selected.value = g
  members.value = await fetchGroupMembers(g.group_pac_id)
  // Mobile: bring the detail (below the list) into view.
  await nextTick()
  detailEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <div class="view split">
    <div class="col">
      <h2>Practice / billing groups</h2>
      <p class="note">Providers sharing a Group PAC ID bill under the same entity.</p>
      <div class="scroll-x" role="region" aria-label="Practice groups" tabindex="0">
        <table class="tbl">
          <thead><tr><th>Group</th><th>PC members</th><th>MD/DO</th><th>NP/PA/CNS</th></tr></thead>
          <tbody>
            <tr v-for="g in groups" :key="g.group_pac_id"
                :class="{ sel: selected?.group_pac_id === g.group_pac_id }" @click="pick(g)">
              <td>{{ g.group_name }}</td>
              <td>{{ g.pc_member_count }}</td>
              <td>{{ g.physician_count }}</td>
              <td>{{ g.app_provider_count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="col" ref="detailEl">
      <h3 v-if="selected">{{ selected.group_name }} — members</h3>
      <p v-else class="note">Select a group to see who bills under it.</p>
      <ul v-if="selected" class="members">
        <li v-for="m in members" :key="m.npi">
          {{ m.provider_name }} <small>{{ m.provider_category }} · {{ m.taxonomy_label }}</small>
        </li>
      </ul>
    </div>
  </div>
</template>
