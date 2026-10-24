import { uuid } from "./id";
import { computed, ref } from "vue";
import { get, set, update } from "idb-keyval";
import seed from "./data/seed.json";
import { bill, execute, initEngine } from "./engine";
import type { Actor, Command, Role, State, CartLine } from "./types";
export const state = ref<State>();
export const role = ref<Role>("owner");
export const tenant = ref("juniper");
export const ready = ref(false);
export const failure = ref("");
export const toast = ref("");
export const busy = ref(false);
export const mode = ref<"local" | "api">("local");
export const apiUrl = ref("");
export const connectionError = ref("");
let polling: ReturnType<typeof setInterval> | undefined;
let refreshing = false;
let connectionEpoch = 0;
let bearer = "";
const brandKey = "mise-brand";
export const money = (value: number) =>
  new Intl.NumberFormat("en-NP", {
    style: "currency",
    currency: "NPR",
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  }).format(value / 100);
export const actor = computed<Actor>(() => ({
  role: role.value,
  name:
    role.value === "owner"
      ? "Owner"
      : role.value.charAt(0).toUpperCase() + role.value.slice(1),
}));
export function makeCommand(
  op: string,
  data: unknown,
  key: string = uuid(),
): Command {
  return { op, data, key, now: new Date().toISOString() };
}
export function createSeed(id = "juniper", sample = true): State {
  const s = structuredClone(seed) as State;
  if (id !== "juniper") {
    s.restaurant = {
      ...s.restaurant,
      id,
      slug: "ember-kitchen",
      name: "Ember Kitchen",
      tagline: "Made over fire. Shared with friends.",
      address: "Lazimpat, Kathmandu",
    };
    s.menu = s.menu.slice(0, 6);
  }
  if (!sample) return s;
  const owner: Actor = { role: "owner", name: "Sample service" };
  for (const [table, guests] of [
    [3, 3],
    [4, 4],
    [6, 2],
    [9, 2],
  ] as number[][]) {
    Object.assign(
      s,
      execute(
        s,
        owner,
        makeCommand("open_session", {
          table_id: `table-${table}`,
          guests,
          token: uuid(),
        }),
      ),
    );
    const session = s.sessions.at(-1)!;
    Object.assign(
      s,
      execute(
        s,
        {
          role: table === 6 ? "guest" : "owner",
          name: "Sample service",
          session_id: session.id,
        },
        makeCommand("submit_order", {
          session_id: session.id,
          lines: [
            {
              item_id: `dish-${table === 3 ? 1 : table === 4 ? 3 : table === 6 ? 2 : 4}`,
              quantity: 2,
            },
            {
              item_id: s.menu.some((d) => d.id === "dish-10")
                ? "dish-10"
                : s.menu.at(-1)!.id,
              quantity: 2,
            },
          ],
          note: table === 3 ? "One portion mild, please." : "",
        }),
      ),
    );
    if (table === 3 || table === 9) {
      const o = s.orders.at(-1)!;
      for (let idx = 0; idx < o.lines.length; idx++)
        Object.assign(
          s,
          execute(
            s,
            owner,
            makeCommand("advance_line", {
              order_id: o.id,
              index: idx,
              expected_status: o.lines[idx].status,
            }),
          ),
        );
    }
  }
  const sid = s.sessions.find((x) => x.table_id === "table-4")!.id;
  Object.assign(
    s,
    execute(
      s,
      owner,
      makeCommand("service_request", { session_id: sid, kind: "waiter" }),
    ),
  );
  return s;
}
async function openLocal(id: string) {
  let snapshot: State | undefined;
  await update<State>(`mise:${id}`, (latest) => {
    snapshot = latest || createSeed(id);
    return snapshot;
  });
  return snapshot!;
}
export async function initialize() {
  try {
    await initEngine();
    tenant.value = localStorage.getItem(brandKey) || "juniper";
    state.value = await openLocal(tenant.value);
    ready.value = true;
    window.addEventListener("storage", (e) => {
      if (e.key === "mise-refresh" && mode.value === "local") void refresh();
    });
  } catch (e) {
    failure.value = e instanceof Error ? e.message : String(e);
  }
}
async function persist() {
  await set(`mise:${tenant.value}`, JSON.parse(JSON.stringify(state.value)));
  localStorage.setItem("mise-refresh", uuid());
}
export async function refresh() {
  const epoch = connectionEpoch,
    id = tenant.value,
    origin = apiUrl.value,
    currentMode = mode.value;
  const next =
    currentMode === "local"
      ? await get<State>(`mise:${id}`)
      : await request("/api/state");
  if (
    epoch !== connectionEpoch ||
    id !== tenant.value ||
    origin !== apiUrl.value ||
    currentMode !== mode.value ||
    !next
  )
    return;
  if (
    next.restaurant.id === state.value?.restaurant.id &&
    next.version < (state.value?.version || 0)
  )
    return;
  state.value = next;
}
async function request(path: string, body?: unknown) {
  const res = await fetch(`${apiUrl.value}${path}`, {
    method: body ? "POST" : "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${bearer}`,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const v = await res.json();
  if (!res.ok)
    throw new Error(v.error || "The server could not complete that action.");
  return v;
}
export async function connect(url: string, token: string) {
  const u = new URL(url);
  if (
    u.protocol !== "https:" &&
    !["localhost", "127.0.0.1"].includes(u.hostname)
  )
    throw new Error("Use HTTPS for remote servers.");
  connectionEpoch++;
  clearInterval(polling);
  const old = { url: apiUrl.value, bearer };
  apiUrl.value = url.replace(/\/$/, "");
  bearer = token;
  try {
    const result = await request("/api/me");
    const next = await request("/api/state");
    state.value = next;
    tenant.value = result.tenant;
    role.value = result.role;
    mode.value = "api";
    polling = setInterval(async () => {
      if (refreshing || busy.value) return;
      refreshing = true;
      try {
        await refresh();
        connectionError.value = "";
      } catch {
        connectionError.value =
          "Connection interrupted. Displayed records may be stale. Reconnect before continuing service.";
      } finally {
        refreshing = false;
      }
    }, 5000);
    toast.value = "Connected to the Python API";
  } catch (e) {
    apiUrl.value = old.url;
    bearer = old.bearer;
    throw e;
  }
}
export async function disconnect() {
  connectionEpoch++;
  mode.value = "local";
  clearInterval(polling);
  connectionError.value = "";
  bearer = "";
  await refresh();
}
export async function switchTenant(id: string) {
  if (mode.value === "api")
    throw new Error("Disconnect the API to switch local workspaces.");
  if (busy.value) throw new Error("Wait for the current save to finish.");
  if (!["juniper", "ember"].includes(id)) throw new Error("Unknown workspace");
  connectionEpoch++;
  tenant.value = id;
  localStorage.setItem(brandKey, id);
  state.value = await openLocal(id);
}
export async function dispatch(
  op: string,
  data: unknown,
  as: Actor = actor.value,
  key?: string,
) {
  if (busy.value) throw new Error("An action is already saving. Please wait.");
  busy.value = true;
  try {
    const cmd = makeCommand(op, data, key);
    if (mode.value === "api") {
      const epoch = connectionEpoch;
      const next = await request("/api/command", cmd);
      if (
        epoch === connectionEpoch &&
        mode.value === "api" &&
        next.version >= (state.value?.version || 0)
      )
        state.value = next;
    } else {
      // IndexedDB's read/write transaction serializes updates across browser tabs.
      let next: State | undefined;
      await update<State>(`mise:${tenant.value}`, (latest) => {
        next = execute(
          latest || JSON.parse(JSON.stringify(state.value)),
          as,
          cmd,
        );
        return next;
      });
      state.value = next!;
      localStorage.setItem("mise-refresh", uuid());
    }
  } finally {
    busy.value = false;
  }
}
export const activeSessions = computed(
  () => state.value?.sessions.filter((s) => !s.closed) || [],
);
export const pending = computed(
  () => state.value?.orders.filter((o) => o.status === "pending") || [],
);
export const requests = computed(
  () => state.value?.requests.filter((r) => !r.resolved) || [],
);
export function sessionBill(id: string) {
  return bill(state.value!, id);
}
export async function resetLocal() {
  if (mode.value === "api")
    throw new Error("Reset is only available for local sample data.");
  state.value = createSeed(tenant.value, false);
  await persist();
}
export function csvExport() {
  const s = state.value!;
  const quote = (x: unknown) => `"${String(x).replaceAll('"', '""')}"`;
  const rows = [
    ["payment", "visit", "amount_minor", "method", "received_at"],
    ...s.payments.map((p) => [
      p.id,
      p.session_id,
      p.amount,
      p.method,
      p.created,
    ]),
  ];
  const a = document.createElement("a");
  a.href = URL.createObjectURL(
    new Blob([rows.map((r) => r.map(quote).join(",")).join("\r\n")], {
      type: "text/csv",
    }),
  );
  a.download = `mise-payments-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}
export type { CartLine };
