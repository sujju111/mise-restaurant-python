<script setup lang="ts">
import { asset } from "../assets";

import { uuid } from "../id";

import { computed, onMounted, onUnmounted, ref } from "vue";
import {
  state,
  money,
  dispatch,
  sessionBill,
  toast,
  mode,
  apiUrl,
} from "../store";
import type { CartLine, Restaurant, Dish, Order, Bill } from "../types";
import StatusPill from "./StatusPill.vue";
const props = defineProps<{ token: string; standalone: boolean }>();
const emit = defineEmits<{ close: [] }>();
const category = ref("All");
const search = ref("");
const cart = ref<CartLine[]>([]);
const note = ref("");
const cartOpen = ref(false);
const orderOpen = ref(false);
const saving = ref(false);
const error = ref("");
const retryKey = ref(uuid());
const remote = ref<{
  restaurant: Restaurant;
  menu: Dish[];
  session?: { id: string; table_id: string; guests: number };
  orders?: Order[];
  bill?: Bill;
}>();
const base = computed(() => apiUrl.value || import.meta.env.VITE_API_URL || "");
const isRemote = computed(
  () => mode.value === "api" || !!import.meta.env.VITE_API_URL,
);
const restaurant = computed(
  () => remote.value?.restaurant || state.value!.restaurant,
);
const menu = computed(() => remote.value?.menu || state.value!.menu);
const session = computed(() =>
  isRemote.value
    ? remote.value?.session
    : state.value!.sessions.find((s) => s.token === props.token && !s.closed),
);
const orders = computed(() =>
  isRemote.value
    ? remote.value?.orders || []
    : state.value!.orders.filter((o) => o.session_id === session.value?.id),
);
const bill = computed(() =>
  isRemote.value
    ? remote.value?.bill
    : session.value
      ? sessionBill(session.value.id)
      : undefined,
);
const categories = computed(() => [
  "All",
  ...new Set(menu.value.map((d) => d.category)),
]);
const dishes = computed(() =>
  menu.value.filter(
    (d) =>
      (category.value === "All" || d.category === category.value) &&
      `${d.name} ${d.description}`
        .toLowerCase()
        .includes(search.value.toLowerCase()),
  ),
);
const quantity = computed(() => cart.value.reduce((a, l) => a + l.quantity, 0));
const total = computed(() =>
  cart.value.reduce(
    (a, l) =>
      a + (menu.value.find((d) => d.id === l.item_id)?.price || 0) * l.quantity,
    0,
  ),
);
function add(id: string) {
  if (!session.value) {
    toast.value = "Ask your waiter for the current table QR to place an order.";
    return;
  }
  const line = cart.value.find((l) => l.item_id === id);
  if (line) {
    if (line.quantity < 30) line.quantity++;
  } else cart.value.push({ item_id: id, quantity: 1 });
}
async function load() {
  if (!isRemote.value) return;
  try {
    const slug =
      new URLSearchParams(location.search).get("menu") ||
      state.value!.restaurant.slug;
    const path = props.token
      ? `/api/guest/${encodeURIComponent(props.token)}`
      : `/api/menu/${encodeURIComponent(slug)}`;
    const r = await fetch(base.value + path);
    const v = await r.json();
    if (!r.ok) {
      if (r.status === 404) {
        remote.value = undefined;
        cart.value = [];
        cartOpen.value = false;
        orderOpen.value = false;
      }
      throw new Error(v.error);
    }
    remote.value = v;
    error.value = "";
  } catch (e) {
    error.value = (e as Error).message;
  }
}
async function action(op: string, data: unknown, key = uuid()) {
  if (isRemote.value) {
    const r = await fetch(
      `${base.value}/api/guest/${encodeURIComponent(props.token)}/command`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ op, data, key, now: new Date().toISOString() }),
      },
    );
    const v = await r.json();
    if (!r.ok) throw new Error(v.error);
    await load();
  } else
    await dispatch(
      op,
      data,
      { role: "guest", name: "Guest", session_id: session.value!.id },
      key,
    );
}
async function submit() {
  if (!session.value || saving.value) return;
  saving.value = true;
  error.value = "";
  try {
    await action(
      "submit_order",
      { session_id: session.value.id, lines: cart.value, note: note.value },
      retryKey.value,
    );
    cart.value = [];
    note.value = "";
    cartOpen.value = false;
    orderOpen.value = true;
    retryKey.value = uuid();
    toast.value = "Your order is with the team, waiting for approval.";
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    saving.value = false;
  }
}
async function request(kind: string) {
  if (!session.value) return;
  try {
    await action("service_request", { session_id: session.value.id, kind });
    toast.value =
      kind === "bill"
        ? "The team will bring your bill."
        : "Your waiter has been notified.";
  } catch (e) {
    toast.value = (e as Error).message;
  }
}
let polling: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
  void load();
  if (isRemote.value) polling = setInterval(() => void load(), 5000);
});
onUnmounted(() => clearInterval(polling));
</script>
<template>
  <div v-if="isRemote && !remote" class="boot-screen">
    <img :src="asset('mark.svg')" alt="Mise" />
    <h1>
      {{
        error ? "We couldn’t open this menu." : "Something good is on the way."
      }}
    </h1>
    <p>{{ error || "Loading your restaurant…" }}</p>
    <v-btn v-if="error" color="primary" @click="load">Try again</v-btn
    ><v-btn v-if="!standalone" variant="text" @click="emit('close')"
      >Return to workspace</v-btn
    >
  </div>
  <div v-else class="guest-page">
    <div class="guest-top">
      <a class="guest-wordmark" href="#" @click.prevent
        >{{ restaurant.name }}<span>✳</span></a
      >
      <div>
        <span class="guest-table"
          ><v-icon icon="mdi-table-furniture" size="17" />{{
            session
              ? state!.tables.find((t) => t.id === session!.table_id)?.name ||
                session.table_id
              : "THE MENU"
          }}</span
        ><v-btn
          v-if="!standalone"
          class="ml-2"
          icon="mdi-close"
          variant="text"
          aria-label="Return to staff workspace"
          @click="emit('close')"
        />
      </div>
    </div>
    <div class="guest-hero">
      <img
        :src="asset('images/salad.jpg')"
        alt="A seasonal plate, prepared with care"
      />
      <div class="guest-hero-overlay">
        <div class="eyebrow">A TABLE WORTH SHARING</div>
        <h1>Stay a little.<br /><em>Eat something good.</em></h1>
        <p>{{ restaurant.tagline }}</p>
      </div>
      <span class="guest-seal">FRESH<br />✳<br />WITH CARE</span>
    </div>
    <main class="guest-main">
      <div class="guest-welcome">
        <div>
          <span class="eyebrow"
            >WELCOME TO {{ restaurant.name.toUpperCase() }}</span
          >
          <h2>What sounds good?</h2>
          <p>Made in our kitchen. Meant for your table.</p>
        </div>
        <div v-if="session" class="guest-service">
          <button @click="request('waiter')">
            <v-icon icon="mdi-hand-wave-outline" size="20" />Call waiter</button
          ><button @click="orderOpen = true">
            <v-icon icon="mdi-receipt-text-outline" size="20" />My table
            <b v-if="orders.length">{{ orders.length }}</b>
          </button>
        </div>
      </div>
      <v-alert
        v-if="props.token && !session && !isRemote"
        type="info"
        variant="tonal"
        class="mb-5"
        >This visit has ended, or this QR belongs to another device’s local
        demo. Ask your waiter for the current table link.</v-alert
      ><v-alert
        v-else-if="!props.token"
        type="info"
        variant="tonal"
        class="mb-5"
        density="compact"
        >You’re browsing the menu. Scan your table’s current QR code to
        order.</v-alert
      ><v-alert v-if="error" type="error" variant="tonal" class="mb-5">{{
        error
      }}</v-alert>
      <div class="guest-menu-tools">
        <div class="category-tabs">
          <button
            v-for="c in categories"
            :key="c"
            :class="{ active: category === c }"
            @click="category = c"
          >
            {{ c }}
          </button>
        </div>
        <v-text-field
          v-model="search"
          placeholder="Find your favourite…"
          aria-label="Search guest menu"
          prepend-inner-icon="mdi-magnify"
          hide-details
          density="compact"
        />
      </div>
      <div class="guest-dish-grid">
        <article
          v-for="d in dishes"
          :key="d.id"
          class="guest-dish"
          :class="{ 'sold-out': !d.available }"
        >
          <div class="guest-dish-photo">
            <img
              :src="asset(`images/${d.image}.jpg`)"
              :alt="d.name"
              loading="lazy"
            /><span v-if="d.dietary" class="dietary-tag">{{ d.dietary }}</span>
          </div>
          <div class="guest-dish-copy">
            <small>{{ d.category }}</small>
            <h3>{{ d.name }}</h3>
            <p>{{ d.description }}</p>
            <div>
              <strong>{{ money(d.price) }}</strong
              ><button
                :disabled="!d.available || !session"
                :aria-label="`Add ${d.name} to order`"
                @click="add(d.id)"
              >
                {{ d.available ? "Add to order" : "Sold out"
                }}<v-icon v-if="d.available" icon="mdi-plus" size="18" />
              </button>
            </div>
          </div>
        </article>
      </div>
      <div v-if="!dishes.length" class="empty-state">
        <h3>Nothing here just yet.</h3>
        <p>Try a different category or search.</p>
      </div>
      <div class="guest-bottom-note">
        <span>✳</span>
        <h3>Good food is better together.</h3>
        <p>
          Tell your waiter about allergies before ordering. Dietary labels
          aren’t an allergen guarantee.
        </p>
        <small>{{ restaurant.address }} · Powered by mise.</small>
      </div>
    </main>
    <button v-if="quantity" class="floating-cart" @click="cartOpen = true">
      <span class="cart-count">{{ quantity }}</span
      ><span>View your order</span><strong>{{ money(total) }}</strong
      ><v-icon icon="mdi-arrow-right" size="20" />
    </button>
  </div>
  <v-dialog v-model="cartOpen"
    ><v-card class="dialog-card"
      ><div class="row-between">
        <h2>A little of what you love.</h2>
        <v-btn
          icon="mdi-close"
          variant="text"
          aria-label="Close cart"
          @click="cartOpen = false"
        />
      </div>
      <div v-for="(l, index) in cart" :key="l.item_id" class="cart-row">
        <div>
          <strong>{{ menu.find((d) => d.id === l.item_id)?.name }}</strong>
          <p class="muted">
            {{
              money(
                (menu.find((d) => d.id === l.item_id)?.price || 0) * l.quantity,
              )
            }}
          </p>
        </div>
        <div class="quantity-stepper">
          <button
            :aria-label="`Remove ${l.item_id}`"
            @click="l.quantity > 1 ? l.quantity-- : cart.splice(index, 1)"
          >
            −</button
          ><span>{{ l.quantity }}</span
          ><button
            :aria-label="`Add ${l.item_id}`"
            :disabled="l.quantity >= 30"
            @click="l.quantity++"
          >
            +
          </button>
        </div>
      </div>
      <v-textarea
        v-model="note"
        class="mt-5"
        variant="outlined"
        label="Anything the kitchen should know?"
        rows="2"
        maxlength="500"
      /><v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{
        error
      }}</v-alert>
      <div class="row-between mb-4">
        <strong>Food subtotal</strong><strong>{{ money(total) }}</strong>
      </div>
      <p class="tiny-note mb-4">
        Tax {{ restaurant.tax_bps / 100 }}% · Service
        {{ restaurant.service_bps / 100 }}%. Your waiter confirms your order
        before cooking begins. Final charges appear on your table’s bill.
      </p>
      <v-btn
        block
        color="primary"
        :loading="saving"
        :disabled="!cart.length || !session"
        @click="submit"
        >Send order for approval</v-btn
      ></v-card
    ></v-dialog
  >
  <v-dialog v-model="orderOpen"
    ><v-card class="dialog-card"
      ><div class="row-between">
        <h2>Your table, taken care of.</h2>
        <v-btn
          icon="mdi-close"
          variant="text"
          aria-label="Close table orders"
          @click="orderOpen = false"
        />
      </div>
      <p class="muted mb-5">
        Keep the conversation going. We’ll handle the rest.
      </p>
      <div v-for="o in orders" :key="o.id" class="guest-order">
        <div class="row-between">
          <strong>{{ o.id }}</strong
          ><StatusPill :status="o.status" />
        </div>
        <p v-for="(l, index) in o.lines" :key="index" class="muted mt-2">
          {{ l.quantity }} × {{ l.name }}
        </p>
      </div>
      <p v-if="!orders.length" class="muted my-5">
        Your first order will appear here.
      </p>
      <div v-if="bill" class="receipt-totals">
        <div>
          <span>Accepted bill total</span
          ><strong>{{ money(bill.total) }}</strong>
        </div>
        <div>
          <span>Payments recorded</span><span>{{ money(bill.paid) }}</span>
        </div>
        <div class="grand-total">
          <span>Balance</span><strong>{{ money(bill.balance) }}</strong>
        </div>
      </div>
      <v-btn
        block
        color="primary"
        class="mt-5"
        :disabled="!session"
        @click="request('bill')"
        >Ask for the bill</v-btn
      >
      <p class="tiny-note">
        Pay at the cashier. Online payments aren’t connected.
      </p></v-card
    ></v-dialog
  >
</template>
