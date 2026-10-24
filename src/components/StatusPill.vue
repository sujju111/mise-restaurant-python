<script setup lang="ts">
defineProps<{ status: string }>();
const names: Record<string, string> = {
  pending: "Needs approval",
  accepted: "In queue",
  preparing: "Preparing",
  ready: "Ready to serve",
  served: "Served",
  rejected: "Declined",
  available: "Available",
  occupied: "Seated",
  dirty: "Needs reset",
  queued: "In queue",
};
</script>
<template>
  <span class="status-pill" :class="status"
    ><span class="status-dot"></span>{{ names[status] || status }}</span
  >
</template>
