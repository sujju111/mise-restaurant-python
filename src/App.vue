<script setup lang="ts">
import { asset } from "./assets";

import { computed, onMounted, ref, watch } from "vue";
import {
  initialize,
  state,
  ready,
  failure,
  connectionError,
  role,
  tenant,
  switchTenant,
  mode,
  toast,
  pending,
  requests,
  money,
  activeSessions,
  sessionBill,
  dispatch,
  busy,
  connect,
  disconnect,
  resetLocal,
  csvExport,
} from "./store";
import type { Role, Session } from "./types";
import FloorView from "./components/FloorView.vue";
import MenuView from "./components/MenuView.vue";
import KitchenView from "./components/KitchenView.vue";
import GuestView from "./components/GuestView.vue";
import SessionDrawer from "./components/SessionDrawer.vue";
import StatusPill from "./components/StatusPill.vue";
const reload = () => location.reload();
const page = ref("Overview");
const mobileNav = ref(false);
const selected = ref<Session>();
const guest = ref(false);
const config = ref(false);
const resetDialog = ref(false);
const apiForm = ref({ url: "http://localhost:8080", token: "" });
const connecting = ref(false);
const nav = [
  ["Overview", "mdi-view-dashboard-outline"],
  ["Floor & tables", "mdi-floor-plan"],
  ["Orders", "mdi-receipt-text-outline"],
  ["Kitchen", "mdi-chef-hat"],
  ["Menu studio", "mdi-silverware-fork-knife"],
  ["Payments", "mdi-credit-card-outline"],
  ["Inventory", "mdi-package-variant-closed"],
  ["Reports", "mdi-chart-box-outline"],
  ["Activity", "mdi-history"],
  ["Settings", "mdi-tune-variant"],
];
const allowed: Record<Role, string[]> = {
  owner: nav.map((n) => n[0]),
  waiter: ["Floor & tables", "Orders"],
  kitchen: ["Kitchen"],
  cashier: ["Payments", "Orders"],
  guest: [],
};
const visibleNav = computed(() =>
  nav.filter((n) => allowed[role.value].includes(n[0])),
);
watch(role, () => {
  if (!allowed[role.value].includes(page.value))
    page.value = allowed[role.value][0] || "Overview";
});
watch(tenant, () => {
  selected.value = undefined;
  guest.value = false;
});
const kitchenCount = computed(
  () =>
    state.value?.orders.filter((o) =>
      ["accepted", "preparing", "ready"].includes(o.status),
    ).length || 0,
);
const collected = computed(
  () => state.value?.payments.reduce((a, p) => a + p.amount, 0) || 0,
);
const sales = computed(
  () =>
    state.value?.sessions.reduce((a, s) => a + sessionBill(s.id).total, 0) || 0,
);
const greeting = computed(() =>
  new Date().getHours() < 12
    ? "Good morning"
    : new Date().getHours() < 17
      ? "Good afternoon"
      : "Good evening",
);
const today = new Intl.DateTimeFormat("en", {
  weekday: "long",
  month: "long",
  day: "numeric",
}).format(new Date());
const settings = ref({
  name: "",
  tagline: "",
  address: "",
  tax_bps: 0,
  service_bps: 0,
});
watch(
  () => state.value?.restaurant,
  (r) => {
    if (r) settings.value = { ...r };
  },
  { immediate: true },
);
const stockDialog = ref(false);
const stockForm = ref({ stock_id: "", delta: 0, reason: "" });
async function act(op: string, data: unknown) {
  try {
    await dispatch(op, data);
    toast.value = "Saved";
    return true;
  } catch (e) {
    toast.value = (e as Error).message;
    return false;
  }
}
async function changeTenant(id: string) {
  try {
    await switchTenant(id);
  } catch (e) {
    toast.value = (e as Error).message;
  }
}
async function apiConnect() {
  connecting.value = true;
  try {
    await connect(apiForm.value.url, apiForm.value.token);
    apiForm.value.token = "";
    config.value = false;
  } catch (e) {
    toast.value = (e as Error).message;
  } finally {
    connecting.value = false;
  }
}
const guestToken = ref(new URLSearchParams(location.search).get("visit") || "");
const restaurantSlug = new URLSearchParams(location.search).get("menu");
const guestRoute = !!(guestToken.value || restaurantSlug);
onMounted(async () => {
  await initialize();
  if (
    ready.value &&
    restaurantSlug &&
    ![state.value?.restaurant.slug].includes(restaurantSlug)
  ) {
    const id =
      restaurantSlug === "ember-kitchen"
        ? "ember"
        : restaurantSlug === "juniper-house"
          ? "juniper"
          : "";
    if (id) await changeTenant(id);
    else failure.value = "This restaurant menu was not found.";
  }
});
function viewGuest() {
  guest.value = true;
  guestToken.value = selected.value?.token || "";
}
function navigate(name: string) {
  page.value = name;
  mobileNav.value = false;
}
</script>
<template>
  <v-app>
    <div v-if="failure" class="boot-screen">
      <img :src="asset('mark.svg')" alt="" />
      <h1>Let’s get you back to service.</h1>
      <p role="alert">{{ failure }}</p>
      <v-btn @click="reload()">Reload workspace</v-btn>
    </div>
    <div v-else-if="!ready" class="boot-screen">
      <img :src="asset('mark.svg')" alt="Mise" />
      <h1>A calmer kind of service.</h1>
      <v-progress-circular indeterminate color="primary" size="24" />
      <p>Opening your restaurant workspace…</p>
    </div>
    <template v-else-if="state">
      <GuestView
        v-if="guestRoute || guest"
        :token="guestToken"
        :standalone="guestRoute"
        @close="guest = false"
      />
      <div v-else class="workspace">
        <button
          v-if="mobileNav"
          class="nav-backdrop"
          aria-label="Close navigation"
          @click="mobileNav = false"
        ></button>
        <aside class="sidebar" :class="{ 'is-open': mobileNav }">
          <a class="wordmark" href="#" @click.prevent="navigate('Overview')"
            ><img :src="asset('mark.svg')" alt="" /><span
              >mise<span class="brand-dot">.</span></span
            ></a
          >
          <div class="workspace-switch">
            <span class="overline">YOUR RESTAURANT</span
            ><v-select
              aria-label="Restaurant workspace"
              :model-value="tenant"
              @update:model-value="changeTenant"
              :items="[
                { title: 'Juniper House', value: 'juniper' },
                { title: 'Ember Kitchen', value: 'ember' },
              ]"
              hide-details
              :disabled="mode === 'api'"
            /><span class="workspace-note"
              ><i class="live-dot"></i
              >{{
                mode === "local"
                  ? "Local workspace · sample service"
                  : "Connected to Rust API"
              }}</span
            >
          </div>
          <span class="nav-label">WORKSPACE</span>
          <nav aria-label="Main navigation">
            <button
              v-for="[name, icon] in visibleNav"
              :key="name"
              :class="{ active: page === name }"
              @click="navigate(name)"
            >
              <v-icon :icon="icon" size="21" /><span>{{ name }}</span
              ><b
                v-if="name === 'Orders' && pending.length"
                class="nav-count"
                >{{ pending.length }}</b
              >
            </button>
          </nav>
          <div class="sidebar-bottom">
            <div class="service-card">
              <span class="service-icon"
                ><v-icon icon="mdi-leaf" size="22" /></span
              ><strong
                >A little more presence.<br />A little less paperwork.</strong
              >
              <p>Make room for great hospitality.</p>
            </div>
            <button class="user-card" @click="config = true">
              <span class="avatar">{{ role.slice(0, 1).toUpperCase() }}</span
              ><span
                ><strong>{{
                  role === "owner" ? "Owner workspace" : role + " workspace"
                }}</strong
                ><small>{{
                  mode === "local"
                    ? "Demo role · switch views"
                    : "Authenticated staff"
                }}</small></span
              ><v-icon icon="mdi-unfold-more-horizontal" size="18" />
            </button>
          </div>
        </aside>
        <div class="main-shell">
          <header class="topbar">
            <div class="breadcrumb">
              <v-btn
                class="mobile-toggle"
                icon="mdi-menu"
                variant="text"
                aria-label="Open navigation"
                @click="mobileNav = true"
              /><span>{{ state.restaurant.name }}</span
              ><v-icon icon="mdi-chevron-right" size="15" /><strong>{{
                page
              }}</strong>
            </div>
            <div class="topbar-actions">
              <span class="local-badge"
                ><i class="live-dot"></i
                >{{ mode === "local" ? "Local demo" : "API connected" }}</span
              ><v-btn
                variant="outlined"
                prepend-icon="mdi-qrcode-scan"
                @click="viewGuest"
                >Guest menu</v-btn
              ><button
                class="notification"
                aria-label="View service requests"
                @click="navigate('Orders')"
              >
                <v-icon icon="mdi-bell-outline" /><span
                  v-if="requests.length"
                ></span></button
              ><span class="avatar small">{{ role[0].toUpperCase() }}</span>
            </div>
          </header>
          <main id="main" class="page-content">
            <v-alert
              v-if="connectionError"
              type="error"
              variant="tonal"
              class="mb-5"
              >{{ connectionError }}</v-alert
            >
            <template v-if="page === 'Overview'">
              <div class="page-heading">
                <div>
                  <div class="eyebrow">
                    {{ today }} <span class="heading-dot">·</span> SERVICE
                    WORKSPACE
                  </div>
                  <h1>
                    {{ greeting }}<span class="serif-comma">,</span> chef<span
                      class="serif-comma"
                      >.</span
                    >
                  </h1>
                  <p>Good service starts with a clear view. Here’s yours.</p>
                </div>
                <v-btn
                  color="primary"
                  prepend-icon="mdi-plus"
                  size="large"
                  @click="navigate('Floor & tables')"
                  >Seat a table</v-btn
                >
              </div>
              <div class="overview-hero">
                <div class="hero-copy">
                  <span class="hero-kicker"
                    ><span></span> ROOM TO MAKE IT MEMORABLE</span
                  >
                  <h2>Every table.<br /><em>A little more cared for.</em></h2>
                  <p>
                    Your floor, your kitchen, your people.<br />Everything in
                    its right place.
                  </p>
                  <button @click="navigate('Floor & tables')">
                    Open the floor <v-icon icon="mdi-arrow-right" size="20" />
                  </button>
                </div>
                <div class="hero-photo">
                  <img
                    :src="asset('images/salad.jpg')"
                    alt="Freshly prepared seasonal salad"
                  />
                  <div class="photo-caption">
                    <span>THE HOUSE WAY</span>Made with care.<br />Served with
                    intention.
                  </div>
                </div>
                <div class="hero-stamp">
                  GOOD FOOD<br /><span>✳</span><br />GOOD COMPANY
                </div>
              </div>
              <div class="stat-grid">
                <div class="stat-card">
                  <span class="stat-label"
                    >Collected payments<v-icon
                      icon="mdi-cash-multiple"
                      size="20" /></span
                  ><strong>{{ money(collected) }}</strong
                  ><small>Recorded cash · current dataset</small>
                </div>
                <div class="stat-card">
                  <span class="stat-label"
                    >Tables in service<v-icon
                      icon="mdi-table-furniture"
                      size="20" /></span
                  ><strong
                    >{{ activeSessions.length
                    }}<span> / {{ state.tables.length }}</span></strong
                  ><small
                    >{{
                      state.tables.length -
                      activeSessions.length -
                      state.tables.filter((t) => t.dirty).length
                    }}
                    ready to welcome guests</small
                  >
                </div>
                <div class="stat-card">
                  <span class="stat-label"
                    >Kitchen tickets<v-icon
                      icon="mdi-chef-hat"
                      size="20" /></span
                  ><strong>{{
                    kitchenCount.toString().padStart(2, "0")
                  }}</strong
                  ><small>Accepted, preparing or ready</small>
                </div>
                <div class="stat-card attention">
                  <span class="stat-label"
                    >Needs your attention<v-icon
                      icon="mdi-tray-alert"
                      size="20" /></span
                  ><strong>{{
                    (pending.length + requests.length)
                      .toString()
                      .padStart(2, "0")
                  }}</strong
                  ><small
                    >{{ pending.length }} orders · {{ requests.length }} service
                    requests</small
                  >
                </div>
              </div>
              <div class="dashboard-bottom">
                <section class="surface floor-preview">
                  <div class="section-heading">
                    <div>
                      <h2>Around the room</h2>
                      <p>A live look at your floor.</p>
                    </div>
                    <button
                      class="text-link"
                      @click="navigate('Floor & tables')"
                    >
                      View all tables
                      <v-icon icon="mdi-arrow-top-right" size="17" />
                    </button>
                  </div>
                  <FloorView compact @select="selected = $event" />
                </section>
                <section class="surface attention-panel">
                  <div class="section-heading">
                    <div>
                      <h2>The next little thing</h2>
                      <p>A few things that keep service moving.</p>
                    </div>
                    <span class="mini-badge">{{
                      pending.length + requests.length
                    }}</span>
                  </div>
                  <div
                    v-if="!pending.length && !requests.length"
                    class="empty-state"
                  >
                    <v-icon icon="mdi-check-all" />
                    <h3>All caught up.</h3>
                    <p>Take a breath. Your room is in good hands.</p>
                  </div>
                  <button
                    v-for="order in pending.slice(0, 2)"
                    :key="order.id"
                    class="attention-row"
                    @click="
                      selected = state!.sessions.find(
                        (s) => s.id === order.session_id,
                      )
                    "
                  >
                    <span class="attention-icon"
                      ><v-icon icon="mdi-receipt-text-outline" /></span
                    ><span
                      ><strong
                        >{{
                          state!.tables.find(
                            (t) =>
                              t.id ===
                              state!.sessions.find(
                                (s) => s.id === order.session_id,
                              )?.table_id,
                          )?.name
                        }}
                        · New QR order</strong
                      ><small
                        >{{
                          order.lines.reduce((a, l) => a + l.quantity, 0)
                        }}
                        items waiting for your approval</small
                      ></span
                    ><v-icon icon="mdi-chevron-right" size="18" /></button
                  ><button
                    v-for="request in requests.slice(0, 2)"
                    :key="request.id"
                    class="attention-row"
                    @click="navigate('Orders')"
                  >
                    <span class="attention-icon green"
                      ><v-icon
                        :icon="
                          request.kind === 'bill'
                            ? 'mdi-receipt-outline'
                            : 'mdi-hand-wave-outline'
                        " /></span
                    ><span
                      ><strong>{{
                        state!.tables.find(
                          (t) =>
                            t.id ===
                            state!.sessions.find(
                              (s) => s.id === request.session_id,
                            )?.table_id,
                        )?.name
                      }}</strong
                      ><small>{{
                        request.kind === "bill"
                          ? "Would like the bill"
                          : "Could use a hand"
                      }}</small></span
                    ><v-icon icon="mdi-chevron-right" size="18" />
                  </button>
                  <div class="quiet-note">
                    <v-icon icon="mdi-sprout-outline" size="18" /><span
                      >It’s the small things that bring guests back.</span
                    >
                  </div>
                </section>
              </div>
            </template>
            <template v-else-if="page === 'Floor & tables'"
              ><div class="page-heading">
                <div>
                  <div class="eyebrow">THE HEART OF SERVICE</div>
                  <h1>Make yourself at home.</h1>
                  <p>
                    Choose a table to seat guests, take an order or check in.
                  </p>
                </div>
                <span class="live-label"
                  ><i class="live-dot" />{{ activeSessions.length }} tables in
                  service</span
                >
              </div>
              <FloorView @select="selected = $event"
            /></template>
            <template v-else-if="page === 'Menu studio'"><MenuView /></template>
            <template v-else-if="page === 'Kitchen'"><KitchenView /></template>
            <template v-else-if="page === 'Orders'"
              ><div class="page-heading">
                <div>
                  <div class="eyebrow">KEEP THINGS FLOWING</div>
                  <h1>A little attention.</h1>
                  <p>Review new orders before they reach the kitchen.</p>
                </div>
              </div>
              <div class="two-column">
                <section class="surface padded">
                  <h2>
                    Awaiting approval
                    <span class="mini-badge">{{ pending.length }}</span>
                  </h2>
                  <div v-if="!pending.length" class="empty-state">
                    <v-icon icon="mdi-check-all" />
                    <h3>No orders waiting.</h3>
                    <p>New guest orders appear here.</p>
                  </div>
                  <article
                    v-for="o in pending"
                    :key="o.id"
                    class="order-review"
                  >
                    <div class="row-between">
                      <strong>{{
                        state!.tables.find(
                          (t) =>
                            t.id ===
                            state!.sessions.find((s) => s.id === o.session_id)
                              ?.table_id,
                        )?.name
                      }}</strong
                      ><StatusPill status="pending" />
                    </div>
                    <p v-for="l in o.lines" :key="l.item_id">
                      {{ l.quantity }} × {{ l.name }}
                      <span>{{ money(l.quantity * l.price) }}</span>
                    </p>
                    <div v-if="o.note" class="ticket-note">{{ o.note }}</div>
                    <div class="button-row">
                      <v-btn
                        variant="outlined"
                        :disabled="busy || !['owner', 'waiter'].includes(role)"
                        @click="
                          act('review_order', { order_id: o.id, accept: false })
                        "
                        >Decline</v-btn
                      ><v-btn
                        color="primary"
                        :disabled="busy || !['owner', 'waiter'].includes(role)"
                        @click="
                          act('review_order', { order_id: o.id, accept: true })
                        "
                        >Accept & send to kitchen</v-btn
                      >
                    </div>
                  </article>
                </section>
                <section class="surface padded">
                  <h2>Guest requests</h2>
                  <div v-if="!requests.length" class="empty-state">
                    <v-icon icon="mdi-hand-wave-outline" />
                    <h3>Nothing waiting.</h3>
                    <p>Requests for a waiter or bill appear here.</p>
                  </div>
                  <article
                    v-for="r in requests"
                    :key="r.id"
                    class="request-row"
                  >
                    <div>
                      <strong>{{
                        state!.tables.find(
                          (t) =>
                            t.id ===
                            state!.sessions.find((s) => s.id === r.session_id)
                              ?.table_id,
                        )?.name
                      }}</strong>
                      <p>
                        {{
                          r.kind === "bill"
                            ? "Bill requested"
                            : "Waiter requested"
                        }}
                      </p>
                    </div>
                    <v-btn
                      size="small"
                      variant="outlined"
                      :disabled="busy"
                      @click="act('resolve_request', { request_id: r.id })"
                      >Mark done</v-btn
                    >
                  </article>
                </section>
              </div>
              <section class="surface padded mt-6">
                <h2>All orders</h2>
                <div class="data-table-wrap">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Order</th>
                        <th>Table</th>
                        <th>Items</th>
                        <th>Source</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="o in [...state.orders].reverse()"
                        :key="o.id"
                        @click="
                          selected = state!.sessions.find(
                            (s) => s.id === o.session_id,
                          )
                        "
                      >
                        <td>{{ o.id }}</td>
                        <td>
                          {{
                            state!.tables.find(
                              (t) =>
                                t.id ===
                                state!.sessions.find(
                                  (s) => s.id === o.session_id,
                                )?.table_id,
                            )?.name
                          }}
                        </td>
                        <td>
                          {{
                            o.lines
                              .map((l) => `${l.quantity} × ${l.name}`)
                              .join(", ")
                          }}
                        </td>
                        <td>{{ o.source }}</td>
                        <td><StatusPill :status="o.status" /></td>
                      </tr>
                    </tbody>
                  </table>
                </div></section
            ></template>
            <template v-else-if="page === 'Payments'"
              ><div class="page-heading">
                <div>
                  <div class="eyebrow">A GOOD END TO A GOOD MEAL</div>
                  <h1>Settle in. Settle up.</h1>
                  <p>Every round of orders, together on one running bill.</p>
                </div>
                <v-btn
                  variant="outlined"
                  prepend-icon="mdi-download"
                  @click="csvExport"
                  >Export payments</v-btn
                >
              </div>
              <div class="bill-grid">
                <button
                  v-for="s in activeSessions"
                  :key="s.id"
                  class="surface bill-tile"
                  @click="selected = s"
                >
                  <div class="row-between">
                    <strong>{{
                      state!.tables.find((t) => t.id === s.table_id)?.name
                    }}</strong
                    ><v-icon icon="mdi-arrow-top-right" size="20" />
                  </div>
                  <small
                    >{{ s.guests }} guests ·
                    {{
                      state!.orders.filter((o) => o.session_id === s.id).length
                    }}
                    orders</small
                  ><span>Remaining balance</span>
                  <h2>{{ money(sessionBill(s.id).balance) }}</h2>
                  <p>Collected {{ money(sessionBill(s.id).paid) }}</p>
                </button>
                <div v-if="!activeSessions.length" class="surface empty-state">
                  <v-icon icon="mdi-receipt-check-outline" />
                  <h3>No open bills.</h3>
                  <p>Seat a table to start a new visit.</p>
                </div>
              </div>
              <v-alert
                class="mt-6"
                variant="tonal"
                type="info"
                density="compact"
                >Cash recording is available. Online checkout is not connected
                and cannot mark bills paid.</v-alert
              ></template
            >
            <template v-else-if="page === 'Inventory'"
              ><div class="page-heading">
                <div>
                  <div class="eyebrow">A WELL-STOCKED KITCHEN</div>
                  <h1>The good ingredients.</h1>
                  <p>
                    Manual stock counts. Recipe-based deductions are not
                    enabled.
                  </p>
                </div>
              </div>
              <section class="surface padded">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Ingredient</th>
                      <th>On hand</th>
                      <th>Low-stock threshold</th>
                      <th>Status</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="s in state.stock" :key="s.id">
                      <td>
                        <strong>{{ s.name }}</strong>
                      </td>
                      <td>{{ s.quantity }} {{ s.unit }}</td>
                      <td>{{ s.threshold }} {{ s.unit }}</td>
                      <td>
                        <span
                          class="status-pill"
                          :class="
                            s.quantity <= s.threshold ? 'pending' : 'available'
                          "
                          >{{
                            s.quantity <= s.threshold
                              ? "Restock soon"
                              : "Well stocked"
                          }}</span
                        >
                      </td>
                      <td>
                        <v-btn
                          size="small"
                          variant="outlined"
                          @click="
                            stockForm = {
                              stock_id: s.id,
                              delta: 0,
                              reason: '',
                            };
                            stockDialog = true;
                          "
                          >Adjust</v-btn
                        >
                      </td>
                    </tr>
                  </tbody>
                </table>
              </section></template
            >
            <template v-else-if="page === 'Reports'"
              ><div class="page-heading">
                <div>
                  <div class="eyebrow">A CLEARER PICTURE</div>
                  <h1>Know your service.</h1>
                  <p>
                    Actual records in this workspace, including sample data
                    until cleared.
                  </p>
                </div>
                <v-btn
                  variant="outlined"
                  prepend-icon="mdi-download"
                  @click="csvExport"
                  >Export payments</v-btn
                >
              </div>
              <div class="stat-grid">
                <div class="stat-card">
                  <span class="stat-label">Accepted sales</span
                  ><strong>{{ money(sales) }}</strong
                  ><small>Includes tax and service, excludes pending</small>
                </div>
                <div class="stat-card">
                  <span class="stat-label">Cash collected</span
                  ><strong>{{ money(collected) }}</strong
                  ><small>Recorded payments only</small>
                </div>
                <div class="stat-card">
                  <span class="stat-label">Outstanding</span
                  ><strong>{{ money(sales - collected) }}</strong
                  ><small>Accepted bill totals less payments</small>
                </div>
                <div class="stat-card">
                  <span class="stat-label">Completed visits</span
                  ><strong>{{
                    state.sessions.filter((s) => s.closed).length
                  }}</strong
                  ><small>Settled and closed dining sessions</small>
                </div>
              </div>
              <section class="surface padded">
                <h2>What’s leaving the kitchen</h2>
                <div
                  v-for="dish in state.menu.filter((d) =>
                    state!.orders.some(
                      (o) =>
                        !['pending', 'rejected'].includes(o.status) &&
                        o.lines.some((l) => l.item_id === d.id),
                    ),
                  )"
                  :key="dish.id"
                  class="report-row"
                >
                  <img
                    :src="asset(`images/${dish.image}.jpg`)"
                    alt=""
                  /><strong>{{ dish.name }}</strong
                  ><span
                    >{{
                      state!.orders
                        .filter(
                          (o) => !["pending", "rejected"].includes(o.status),
                        )
                        .flatMap((o) => o.lines)
                        .filter((l) => l.item_id === dish.id)
                        .reduce((a, l) => a + l.quantity, 0)
                    }}
                    sold</span
                  >
                </div>
                <p class="muted mt-4">
                  Sales are not profit. Inventory costs, payroll and refunds are
                  outside this release.
                </p>
              </section></template
            >
            <template v-else-if="page === 'Activity'"
              ><div class="page-heading">
                <div>
                  <div class="eyebrow">THE SERVICE NOTEBOOK</div>
                  <h1>Nothing lost in the rush.</h1>
                  <p>
                    Who did what, and when. Sensitive changes leave a trail.
                  </p>
                </div>
              </div>
              <section class="surface padded">
                <div
                  v-for="a in [...state.audit].reverse().slice(0, 100)"
                  :key="a.id"
                  class="audit-row"
                >
                  <span class="audit-dot"></span>
                  <div>
                    <strong>{{
                      a.action.split(" · ")[0].replaceAll("_", " ")
                    }}</strong>
                    <p>
                      {{ a.actor }} · {{ new Date(a.created).toLocaleString() }}
                    </p>
                  </div>
                </div>
                <div v-if="!state.audit.length" class="empty-state">
                  <h3>A fresh start.</h3>
                  <p>Actions will appear as service begins.</p>
                </div>
              </section></template
            >
            <template v-else-if="page === 'Settings'"
              ><div class="page-heading">
                <div>
                  <div class="eyebrow">MAKE IT YOURS</div>
                  <h1>Your place. Your way.</h1>
                  <p>Restaurant details stay with this owner’s workspace.</p>
                </div>
              </div>
              <div class="two-column">
                <section class="surface padded">
                  <h2>Restaurant identity</h2>
                  <v-form
                    class="settings-form"
                    @submit.prevent="act('update_restaurant', settings)"
                    ><v-text-field
                      v-model="settings.name"
                      label="Restaurant name"
                      required
                      maxlength="100"
                    /><v-text-field
                      v-model="settings.tagline"
                      label="A line that sounds like you"
                      required
                      maxlength="200"
                    /><v-text-field
                      v-model="settings.address"
                      label="Address"
                      required
                      maxlength="200"
                    />
                    <div class="two-fields">
                      <v-text-field
                        v-model.number="settings.tax_bps"
                        type="number"
                        label="Tax in basis points"
                        hint="100 basis points = 1%"
                        persistent-hint
                      /><v-text-field
                        v-model.number="settings.service_bps"
                        type="number"
                        label="Service in basis points"
                        hint="Default 0; configure for your business"
                        persistent-hint
                      />
                    </div>
                    <p class="muted">
                      Billing rates can change only when every visit is closed.
                    </p>
                    <v-btn type="submit" color="primary" :disabled="busy"
                      >Save restaurant</v-btn
                    ></v-form
                  >
                </section>
                <div>
                  <section class="surface padded">
                    <h2>Your guest menu</h2>
                    <p class="muted mt-3">
                      {{ state.restaurant.slug }} · a dedicated menu, with your
                      dishes and pricing.
                    </p>
                    <v-btn
                      class="mt-4"
                      variant="outlined"
                      prepend-icon="mdi-arrow-top-right"
                      @click="viewGuest"
                      >Preview menu</v-btn
                    >
                  </section>
                  <section class="surface padded mt-6">
                    <h2>Ready for a real service?</h2>
                    <p class="muted mt-3">
                      Clear sample visits, orders, payments and activity. Menu
                      and ingredient defaults remain. This affects this local
                      workspace.
                    </p>
                    <v-btn
                      class="mt-4"
                      variant="outlined"
                      color="error"
                      :disabled="mode === 'api'"
                      @click="resetDialog = true"
                      >Clear sample service</v-btn
                    >
                  </section>
                  <section class="surface padded mt-6">
                    <h2>Connect your backend</h2>
                    <p class="muted mt-3">
                      Use the included Rust + SQLite server when you’re ready
                      for shared devices.
                    </p>
                    <v-btn
                      class="mt-4"
                      variant="outlined"
                      @click="config = true"
                      >Connection settings</v-btn
                    >
                  </section>
                </div>
              </div></template
            >
            <footer class="page-footer">
              <span>mise. <span>Made for the art of hospitality.</span></span
              ><span
                >{{
                  mode === "local"
                    ? "Persistent local demo · Rust engine"
                    : "Rust API · shared workspace"
                }}
                <i class="live-dot"
              /></span>
            </footer>
          </main>
        </div>
        <SessionDrawer
          v-if="selected"
          :session-id="selected.id"
          @close="selected = undefined"
          @guest="
            guestToken = $event;
            guest = true;
          "
        />
      </div>
    </template>
    <v-dialog v-model="config"
      ><v-card class="dialog-card"
        ><div class="row-between">
          <h2>Workspace preferences</h2>
          <v-btn
            icon="mdi-close"
            variant="text"
            aria-label="Close preferences"
            @click="config = false"
          />
        </div>
        <template v-if="mode === 'local'"
          ><p class="muted mb-5">
            Local mode runs the real Rust engine on this device. Role switching
            is for testing, not authentication.
          </p>
          <v-select
            v-model="role"
            :items="['owner', 'waiter', 'kitchen', 'cashier']"
            label="Demo role"
          />
          <h3 class="mb-4">Connect to your Rust server</h3>
          <v-text-field v-model="apiForm.url" label="API URL" /><v-text-field
            v-model="apiForm.token"
            label="Staff bearer token"
            type="password"
            autocomplete="off"
          /><v-btn
            block
            color="primary"
            :loading="connecting"
            @click="apiConnect"
            >Connect securely</v-btn
          ></template
        ><template v-else
          ><p class="muted mb-5">
            Authenticated as {{ role }}. Your token is kept in memory and
            cleared on reload.
          </p>
          <v-btn
            color="primary"
            @click="
              disconnect();
              config = false;
            "
            >Return to local demo</v-btn
          ></template
        ></v-card
      ></v-dialog
    >
    <v-dialog v-model="stockDialog"
      ><v-card class="dialog-card"
        ><h2>Record a stock movement</h2>
        <p class="muted my-4">
          Positive to receive stock. Negative for use, waste or correction.
        </p>
        <v-form
          @submit.prevent="
            act('adjust_stock', stockForm).then((ok) => {
              if (ok) stockDialog = false;
            })
          "
          ><v-text-field
            v-model.number="stockForm.delta"
            type="number"
            label="Quantity change (whole units)"
            required
          /><v-text-field
            v-model="stockForm.reason"
            label="Reason"
            required
            minlength="3"
          /><v-btn type="submit" color="primary">Save movement</v-btn
          ><v-btn variant="text" @click="stockDialog = false"
            >Cancel</v-btn
          ></v-form
        ></v-card
      ></v-dialog
    >
    <v-dialog v-model="resetDialog"
      ><v-card class="dialog-card"
        ><h2>Start with a clear floor?</h2>
        <p class="muted my-5">
          This clears local sample service records for
          {{ state?.restaurant.name }}. You can’t undo it.
        </p>
        <div class="button-row">
          <v-btn variant="text" @click="resetDialog = false"
            >Keep sample data</v-btn
          ><v-btn
            color="error"
            @click="
              resetLocal();
              resetDialog = false;
            "
            >Clear sample service</v-btn
          >
        </div></v-card
      ></v-dialog
    >
    <v-snackbar
      :model-value="!!toast"
      @update:model-value="toast = ''"
      :timeout="5000"
      color="primary"
      role="status"
      >{{ toast
      }}<template #actions
        ><v-btn variant="text" @click="toast = ''">Dismiss</v-btn></template
      ></v-snackbar
    >
  </v-app>
</template>
