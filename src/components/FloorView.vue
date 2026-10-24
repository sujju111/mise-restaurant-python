<script setup lang="ts">
import { uuid } from "../id";

import { computed, ref } from "vue";
import {
  state,
  activeSessions,
  pending,
  dispatch,
  toast,
  busy,
  role,
} from "../store";
import type { DiningTable, Session } from "../types";
import StatusPill from "./StatusPill.vue";
const props = defineProps<{ compact?: boolean }>();
const emit = defineEmits<{ select: [Session] }>();
const section = ref("All tables");
const filter = ref("All states");
const seating = ref<DiningTable>();
const guests = ref(2);
const error = ref("");
const tables = computed(() =>
  state.value!.tables.filter(
    (t) =>
      (props.compact ? state.value!.tables.indexOf(t) < 6 : true) &&
      (section.value === "All tables" || t.section === section.value) &&
      (filter.value === "All states" || status(t) === filter.value),
  ),
);
function session(t: DiningTable) {
  return activeSessions.value.find((s) => s.table_id === t.id);
}
function status(t: DiningTable) {
  if (t.dirty) return "dirty";
  const s = session(t);
  if (!s) return "available";
  if (pending.value.some((o) => o.session_id === s.id)) return "pending";
  return "occupied";
}
function select(t: DiningTable) {
  const s = session(t);
  if (s) {
    emit("select", s);
    return;
  }
  if (!["owner", "waiter"].includes(role.value)) {
    toast.value = "Only floor staff can seat guests.";
    return;
  }
  seating.value = t;
  guests.value = Math.min(2, t.seats);
  error.value = "";
}
async function seat() {
  try {
    await dispatch("open_session", {
      table_id: seating.value!.id,
      guests: guests.value,
      token: uuid(),
    });
    const s = activeSessions.value.find(
      (s) => s.table_id === seating.value!.id,
    )!;
    seating.value = undefined;
    emit("select", s);
  } catch (e) {
    error.value = (e as Error).message;
  }
}
async function clean() {
  try {
    await dispatch("clean_table", { table_id: seating.value!.id });
    toast.value = "Table reset. Ready for the next guests.";
    seating.value = undefined;
  } catch (e) {
    error.value = (e as Error).message;
  }
}
</script>
<template>
  <div v-if="state" class="floor-view">
    <div v-if="!compact" class="floor-toolbar">
      <div class="segmented">
        <button
          v-for="s in ['All tables', 'Main room', 'Terrace']"
          :key="s"
          :class="{ active: section === s }"
          @click="section = s"
        >
          {{ s }}
        </button>
      </div>
      <v-select
        v-model="filter"
        aria-label="Filter table state"
        :items="[
          { title: 'All states', value: 'All states' },
          { title: 'Available', value: 'available' },
          { title: 'Seated', value: 'occupied' },
          { title: 'Needs approval', value: 'pending' },
          { title: 'Needs reset', value: 'dirty' },
        ]"
        hide-details
        density="compact"
      />
    </div>
    <div class="floor-legend">
      <span><i class="legend-dot available" />Available</span
      ><span><i class="legend-dot occupied" />Seated</span
      ><span><i class="legend-dot pending" />Needs approval</span
      ><span><i class="legend-dot dirty" />Needs reset</span>
    </div>
    <div class="table-grid" :class="{ compact }">
      <button
        v-for="t in tables"
        :key="t.id"
        class="dining-table"
        :class="status(t)"
        @click="select(t)"
      >
        <div class="table-topline">
          <span>{{ t.name }}</span
          ><v-icon icon="mdi-dots-horizontal" size="18" />
        </div>
        <div
          class="table-illustration"
          :class="{ 'six-seats': t.seats === 6, 'two-seats': t.seats === 2 }"
        >
          <span class="seat s1"></span><span class="seat s2"></span
          ><span class="table-surface"
            ><v-icon
              :icon="session(t) ? 'mdi-silverware-fork-knife' : 'mdi-plus'"
              :size="compact ? 20 : 25" /></span
          ><span v-if="t.seats > 2" class="seat s3"></span
          ><span v-if="t.seats > 2" class="seat s4"></span
          ><span v-if="t.seats === 6" class="seat s5"></span
          ><span v-if="t.seats === 6" class="seat s6"></span>
        </div>
        <div class="table-bottom">
          <StatusPill :status="status(t)" /><span
            >{{ session(t)?.guests || t.seats }}
            {{ session(t) ? "guests" : "seats" }}</span
          >
        </div>
      </button>
    </div>
    <div v-if="!tables.length" class="empty-state">
      <h3>No tables match.</h3>
      <p>Try another section or state.</p>
    </div>
  </div>
  <v-dialog :model-value="!!seating" @update:model-value="seating = undefined"
    ><v-card v-if="seating" class="dialog-card"
      ><div class="row-between">
        <h2>{{ seating.name }}</h2>
        <v-btn
          icon="mdi-close"
          variant="text"
          aria-label="Close seating"
          @click="seating = undefined"
        />
      </div>
      <template v-if="seating.dirty"
        ><p class="muted my-5">
          A fresh start for the next party. Reset this table once it’s cleaned.
        </p>
        <v-btn color="primary" :disabled="busy" @click="clean"
          >Mark clean & available</v-btn
        ></template
      ><template v-else
        ><p class="muted my-5">
          {{ seating.section }} · {{ seating.seats }} seats. Let’s welcome your
          next guests.
        </p>
        <v-form @submit.prevent="seat"
          ><v-text-field
            v-model.number="guests"
            label="Number of guests"
            type="number"
            :min="1"
            :max="seating.seats"
            required
          /><v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{
            error
          }}</v-alert
          ><v-btn type="submit" color="primary" block :loading="busy"
            >Open dining session</v-btn
          ></v-form
        ></template
      >
      <p v-if="error && seating.dirty" class="error-text">
        {{ error }}
      </p></v-card
    ></v-dialog
  >
</template>
