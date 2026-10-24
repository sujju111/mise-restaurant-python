<script setup lang="ts">
import { computed } from "vue";
import { state, dispatch, toast, busy, role } from "../store";
import StatusPill from "./StatusPill.vue";
const columns = [
  { name: "On the pass", status: ["accepted"], icon: "mdi-tray-arrow-down" },
  {
    name: "In the making",
    status: ["preparing"],
    icon: "mdi-pot-steam-outline",
  },
  {
    name: "Ready with care",
    status: ["ready"],
    icon: "mdi-check-circle-outline",
  },
];
const tickets = computed(() =>
  state.value!.orders.filter((o) =>
    ["accepted", "preparing", "ready"].includes(o.status),
  ),
);
function table(id: string) {
  return state.value!.tables.find(
    (t) => t.id === state.value!.sessions.find((s) => s.id === id)?.table_id,
  )?.name;
}
async function advance(
  order_id: string,
  index: number,
  expected_status: string,
) {
  try {
    await dispatch("advance_line", { order_id, index, expected_status });
  } catch (e) {
    toast.value = (e as Error).message;
  }
}
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="eyebrow">THE KITCHEN PASS</div>
      <h1>Good things take care.</h1>
      <p>Only staff-approved orders. Every dish, at its own pace.</p>
    </div>
    <span class="live-label"
      ><i class="live-dot" />{{ tickets.length }} active tickets</span
    >
  </div>
  <div class="kitchen-board">
    <section v-for="c in columns" :key="c.name" class="kitchen-column">
      <div class="kitchen-column-title">
        <v-icon :icon="c.icon" size="20" />
        <h2>{{ c.name }}</h2>
        <span>{{
          tickets.filter((o) => c.status.includes(o.status)).length
        }}</span>
      </div>
      <article
        v-for="o in tickets.filter((o) => c.status.includes(o.status))"
        :key="o.id"
        class="kitchen-ticket"
      >
        <div class="ticket-head">
          <strong>{{ table(o.session_id) }}</strong
          ><small>{{
            new Date(o.created).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })
          }}</small>
        </div>
        <div class="ticket-meta">{{ o.id }} <span>·</span> {{ o.source }}</div>
        <div v-if="o.note" class="ticket-note">
          <v-icon icon="mdi-note-text-outline" size="16" />{{ o.note }}
        </div>
        <div v-for="(l, index) in o.lines" :key="index" class="ticket-line">
          <div>
            <span class="quantity-box">{{ l.quantity }}</span
            ><strong>{{ l.name }}</strong>
          </div>
          <div class="ticket-line-actions">
            <StatusPill :status="l.status" /><v-btn
              v-if="l.status !== 'served'"
              size="small"
              :color="l.status === 'ready' ? 'secondary' : 'primary'"
              variant="tonal"
              :disabled="
                busy ||
                (l.status === 'ready'
                  ? !['owner', 'waiter'].includes(role)
                  : !['owner', 'kitchen'].includes(role))
              "
              @click="advance(o.id, index, l.status)"
              >{{
                l.status === "queued"
                  ? "Start"
                  : l.status === "preparing"
                    ? "Mark ready"
                    : "Serve"
              }}</v-btn
            >
          </div>
        </div>
      </article>
      <div
        v-if="!tickets.some((o) => c.status.includes(o.status))"
        class="column-empty"
      >
        A clear pass. A good moment.
      </div>
    </section>
  </div>
</template>
