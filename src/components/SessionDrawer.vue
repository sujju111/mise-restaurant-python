<script setup lang="ts">
import { asset } from "../assets";

import { Capacitor } from "@capacitor/core";
import { uuid } from "../id";

import { computed, ref, watch } from "vue";
import QRCode from "qrcode";
import {
  state,
  role,
  money,
  sessionBill,
  dispatch,
  toast,
  busy,
  mode,
} from "../store";
import type { CartLine } from "../types";
import StatusPill from "./StatusPill.vue";
const props = defineProps<{ sessionId: string }>();
const emit = defineEmits<{ close: []; guest: [string] }>();
const tab = ref("Visit");
const search = ref("");
const cart = ref<CartLine[]>([]);
const note = ref("");
const error = ref("");
const qr = ref("");
const payment = ref(false);
const paymentKey = ref(uuid());
const amount = ref(0);
const submittedKey = ref(uuid());
const session = computed(() =>
  state.value!.sessions.find((s) => s.id === props.sessionId)!,
);
const table = computed(() =>
  state.value!.tables.find((t) => t.id === session.value.table_id)!,
);
const orders = computed(() =>
  state.value!.orders.filter((o) => o.session_id === props.sessionId),
);
const total = computed(() => sessionBill(props.sessionId));
const cartTotal = computed(() =>
  cart.value.reduce(
    (a, l) =>
      a + state.value!.menu.find((d) => d.id === l.item_id)!.price * l.quantity,
    0,
  ),
);
const canOrder = computed(
  () => ["owner", "waiter"].includes(role.value) && !session.value.closed,
);
const canPay = computed(
  () => ["owner", "cashier"].includes(role.value) && !session.value.closed,
);
const menuBase =
  import.meta.env.VITE_MENU_URL ||
  (Capacitor.isNativePlatform()
    ? ""
    : `${location.origin}${location.pathname}`);
const url = computed(() =>
  menuBase
    ? `${menuBase.replace(/\?.*$/, "")}?menu=${state.value!.restaurant.slug}&visit=${encodeURIComponent(session.value.token)}`
    : "",
);
watch(
  url,
  async (u) => {
    qr.value = u
      ? await QRCode.toDataURL(u, {
          width: 280,
          margin: 2,
          color: { dark: "#233d33", light: "#ffffff" },
        })
      : "";
  },
  { immediate: true },
);
watch(
  () => props.sessionId,
  () => {
    cart.value = [];
    tab.value = "Visit";
    error.value = "";
    submittedKey.value = uuid();
  },
);
function add(id: string) {
  const l = cart.value.find((l) => l.item_id === id);
  if (l) {
    if (l.quantity < 30) l.quantity++;
  } else cart.value.push({ item_id: id, quantity: 1 });
}
async function act(op: string, data: unknown) {
  error.value = "";
  try {
    await dispatch(op, data);
    toast.value = "Saved";
    return true;
  } catch (e) {
    error.value = (e as Error).message;
    return false;
  }
}
async function submitOrder() {
  error.value = "";
  try {
    await dispatch(
      "submit_order",
      { session_id: props.sessionId, lines: cart.value, note: note.value },
      undefined,
      submittedKey.value,
    );
    return true;
  } catch (e) {
    error.value = (e as Error).message;
    return false;
  }
}
async function submit() {
  if (await submitOrder()) {
    cart.value = [];
    note.value = "";
    tab.value = "Visit";
    submittedKey.value = uuid();
  }
}
async function pay() {
  error.value = "";
  try {
    await dispatch(
      "pay",
      {
        session_id: props.sessionId,
        amount: Math.round(amount.value * 100),
        method: "cash",
      },
      undefined,
      paymentKey.value,
    );
    payment.value = false;
    toast.value = "Cash recorded";
  } catch (e) {
    error.value = (e as Error).message;
  }
}
async function close() {
  if (await act("close_session", { session_id: props.sessionId }))
    emit("close");
}
function printReceipt() {
  tab.value = "Bill";
  setTimeout(() => window.print(), 100);
}
</script>
<template>
  <v-dialog
    :model-value="true"
    @update:model-value="emit('close')"
    max-width="1000"
    scrollable
    ><v-card class="session-modal"
      ><header class="session-header">
        <div>
          <div class="eyebrow">
            {{ table.section }} · {{ session.guests }} GUESTS
          </div>
          <h2>{{ table.name }} <span class="muted">/ the visit</span></h2>
        </div>
        <v-btn
          icon="mdi-close"
          variant="text"
          aria-label="Close table visit"
          @click="emit('close')"
        />
      </header>
      <div class="session-tabs">
        <button
          v-for="t in ['Visit', 'Take an order', 'Bill', 'Table QR']"
          :key="t"
          :class="{ active: tab === t }"
          @click="tab = t"
        >
          {{ t }}
        </button>
      </div>
      <v-card-text class="session-body"
        ><v-alert
          v-if="error"
          variant="tonal"
          type="error"
          class="mb-4"
          closable
          @click:close="error = ''"
          >{{ error }}</v-alert
        >
        <template v-if="tab === 'Visit'"
          ><div class="row-between mb-5">
            <h3>Every round, together.</h3>
            <span class="status-pill available">{{
              session.closed ? "Visit closed" : "In service"
            }}</span>
          </div>
          <div v-if="!orders.length" class="empty-state">
            <v-icon icon="mdi-silverware-fork-knife" />
            <h3>Let’s start with something good.</h3>
            <p>Take their first order or share the table menu.</p>
            <v-btn
              v-if="canOrder"
              color="primary"
              class="mt-4"
              @click="tab = 'Take an order'"
              >Take an order</v-btn
            >
          </div>
          <article v-for="o in orders" :key="o.id" class="visit-order">
            <div class="row-between">
              <strong
                >{{ o.id }}
                <small class="muted">· {{ o.source }}</small></strong
              ><StatusPill :status="o.status" />
            </div>
            <div v-for="(l, index) in o.lines" :key="index" class="visit-line">
              <span>{{ l.quantity }} × {{ l.name }}</span
              ><strong>{{ money(l.price * l.quantity) }}</strong
              ><v-btn
                v-if="
                  l.status === 'ready' && ['owner', 'waiter'].includes(role)
                "
                variant="tonal"
                color="primary"
                size="small"
                @click="
                  act('advance_line', {
                    order_id: o.id,
                    index,
                    expected_status: l.status,
                  })
                "
                >Mark served</v-btn
              ><StatusPill
                v-else-if="!['pending', 'rejected'].includes(o.status)"
                :status="l.status"
              />
            </div>
            <p v-if="o.note" class="ticket-note">{{ o.note }}</p>
            <div
              v-if="
                o.status === 'pending' && ['owner', 'waiter'].includes(role)
              "
              class="button-row mt-4"
            >
              <v-btn
                variant="outlined"
                :disabled="busy"
                @click="act('review_order', { order_id: o.id, accept: false })"
                >Decline</v-btn
              ><v-btn
                color="primary"
                :disabled="busy"
                @click="act('review_order', { order_id: o.id, accept: true })"
                >Accept & send</v-btn
              >
            </div>
          </article></template
        >
        <template v-else-if="tab === 'Take an order'"
          ><div v-if="!canOrder" class="empty-state">
            <h3>Ordering isn’t available in this view.</h3>
            <p>Only floor staff can add to an open visit.</p>
          </div>
          <div v-else class="pos-grid">
            <div>
              <v-text-field
                v-model="search"
                label="Find a dish"
                prepend-inner-icon="mdi-magnify"
                hide-details
                class="mb-4"
              /><button
                v-for="d in state!.menu.filter(
                  (d) =>
                    d.available &&
                    d.name.toLowerCase().includes(search.toLowerCase()),
                )"
                :key="d.id"
                class="pos-dish"
                @click="add(d.id)"
              >
                <img :src="asset(`images/${d.image}.jpg`)" alt="" /><span
                  ><strong>{{ d.name }}</strong
                  ><small>{{ money(d.price) }}</small></span
                ><v-icon icon="mdi-plus-circle-outline" color="primary" />
              </button>
            </div>
            <aside class="cart-panel">
              <h3>The order</h3>
              <p v-if="!cart.length" class="muted my-6">
                Choose something from the menu.
              </p>
              <div v-for="(l, index) in cart" :key="l.item_id" class="cart-row">
                <strong>{{
                  state!.menu.find((d) => d.id === l.item_id)!.name
                }}</strong>
                <div class="quantity-stepper">
                  <button
                    :aria-label="`Remove one ${l.item_id}`"
                    @click="
                      l.quantity > 1 ? l.quantity-- : cart.splice(index, 1)
                    "
                  >
                    −</button
                  ><span>{{ l.quantity }}</span
                  ><button
                    :aria-label="`Add one ${l.item_id}`"
                    :disabled="l.quantity >= 30"
                    @click="l.quantity++"
                  >
                    +
                  </button>
                </div>
              </div>
              <v-textarea
                v-model="note"
                label="Kitchen notes / allergies"
                variant="outlined"
                rows="2"
                maxlength="500"
                class="mt-5"
              />
              <div class="row-between mb-5">
                <strong>Subtotal</strong><strong>{{ money(cartTotal) }}</strong>
              </div>
              <v-btn
                color="primary"
                block
                :disabled="!cart.length || busy"
                @click="submit"
                >Send to kitchen</v-btn
              >
              <p class="tiny-note">
                Staff orders go straight to the kitchen. Prices are validated by
                Rust.
              </p>
            </aside>
          </div></template
        >
        <template v-else-if="tab === 'Bill'"
          ><div class="receipt" id="receipt">
            <div class="receipt-heading">
              <img :src="asset('mark.svg')" alt="" />
              <h2>{{ state!.restaurant.name }}</h2>
              <p>{{ state!.restaurant.address }}</p>
              <small>Dining bill · {{ session.id }} · {{ table.name }}</small>
            </div>
            <p class="tiny-note">
              {{
                mode === "local"
                  ? "LOCAL DEMO — NOT A TAX INVOICE"
                  : "DINING SUMMARY — NOT A TAX INVOICE"
              }}
            </p>
            <div
              v-for="o in orders.filter(
                (o) => !['pending', 'rejected'].includes(o.status),
              )"
              :key="o.id"
            >
              <div
                v-for="(l, index) in o.lines"
                :key="index"
                class="receipt-line"
              >
                <span>{{ l.quantity }} × {{ l.name }}</span
                ><span>{{ money(l.price * l.quantity) }}</span>
              </div>
            </div>
            <div class="receipt-totals">
              <div>
                <span>Subtotal</span><span>{{ money(total.subtotal) }}</span>
              </div>
              <div>
                <span>Tax ({{ state!.restaurant.tax_bps / 100 }}%)</span
                ><span>{{ money(total.tax) }}</span>
              </div>
              <div>
                <span>Service ({{ state!.restaurant.service_bps / 100 }}%)</span
                ><span>{{ money(total.service) }}</span>
              </div>
              <div class="grand-total">
                <span>Total</span><span>{{ money(total.total) }}</span>
              </div>
              <div>
                <span>Payments recorded</span
                ><span>{{ money(total.paid) }}</span>
              </div>
              <div class="grand-total">
                <span>Balance</span><span>{{ money(total.balance) }}</span>
              </div>
            </div>
            <p class="receipt-thanks">Thank you for sharing a table with us.</p>
          </div>
          <div class="button-row receipt-actions">
            <v-btn
              variant="outlined"
              prepend-icon="mdi-printer-outline"
              @click="printReceipt"
              >Print bill</v-btn
            ><v-btn
              v-if="canPay && total.balance > 0"
              color="primary"
              @click="
                amount = total.balance / 100;
                paymentKey = uuid();
                payment = true;
              "
              >Record cash received</v-btn
            ><v-btn
              v-if="canPay && total.balance === 0"
              color="primary"
              :disabled="busy"
              @click="close"
              >Close visit & reset table</v-btn
            >
          </div>
          <p
            v-if="orders.some((o) => o.status === 'pending')"
            class="tiny-note"
          >
            Pending orders are excluded. Review them before taking payment.
          </p></template
        >
        <template v-else
          ><div class="qr-panel">
            <div class="eyebrow">YOUR TABLE, YOUR MOMENT</div>
            <h2>A menu in their hands.</h2>
            <p>{{ state!.restaurant.name }} · {{ table.name }}</p>
            <img
              v-if="qr"
              class="table-qr"
              :src="qr"
              alt="QR code for this table’s current dining session"
            /><v-btn
              color="primary"
              prepend-icon="mdi-arrow-top-right"
              @click="emit('guest', session.token)"
              >Open this table’s guest menu</v-btn
            ><v-alert
              v-if="!url"
              variant="tonal"
              type="info"
              density="compact"
              class="mt-5"
              >Guest sharing needs a hosted menu URL. Set VITE_MENU_URL and
              VITE_API_URL before distributing table QR codes. You can try the
              guest flow on this device below.</v-alert
            >
            <p class="tiny-note">
              This link expires when the visit closes. A new party gets a new
              QR.
            </p>
            <v-alert
              v-if="mode === 'local'"
              variant="tonal"
              type="info"
              density="compact"
              >Local demo: orders are shared across tabs on this browser. Other
              phones need the connected backend and a reachable web
              URL.</v-alert
            >
            <p class="tiny-note qr-url">{{ url }}</p>
          </div></template
        >
      </v-card-text></v-card
    ></v-dialog
  ><v-dialog v-model="payment" max-width="440"
    ><v-card class="dialog-card"
      ><h2>Cash in hand.</h2>
      <p class="muted my-5">
        Record money you have actually received. Remaining
        {{ money(total.balance) }}.
      </p>
      <v-form @submit.prevent="pay"
        ><v-text-field
          v-model.number="amount"
          label="Cash received (NPR)"
          type="number"
          min="0.01"
          step="0.01"
          :max="total.balance / 100"
          required
        /><v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{
          error
        }}</v-alert
        ><v-btn block type="submit" color="primary" :disabled="busy"
          >Confirm received cash</v-btn
        ><v-btn block variant="text" class="mt-2" @click="payment = false"
          >Cancel</v-btn
        ></v-form
      ></v-card
    ></v-dialog
  >
</template>
