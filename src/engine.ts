/**
 * Browser-local engine for Mise's offline single-device demo.
 * Shared multi-device service uses the Python server as the authority.
 * This preserves the original frontend execute() and bill() signatures.
 */
import type {Actor, Bill, Command, State} from "./types";

function reject(message: string): never { throw new Error(message); }
function field(data: Record<string, unknown>, name: string): string {
  const text = data[name];
  if (typeof text !== "string") reject("Missing " + name);
  const value = text.trim();
  if (!value || new TextEncoder().encode(value).length > 500) reject("Invalid " + name);
  return value;
}
function integer(data: Record<string, unknown>, name: string, min: number, max: number): number {
  const value = data[name];
  if (typeof value !== "number" || !Number.isInteger(value)) reject("Invalid " + name);
  if (value < min || value > max) reject(name + " must be between " + min + " and " + max);
  return value;
}
function permit(actor: Actor, ...roles: string[]) {
  if (!roles.includes(actor.role)) reject("Your role cannot perform this action");
}
function nextId(s: State, prefix: string): string {
  s.sequence++;
  return prefix + "-" + s.sequence;
}
function active(s: State, sid: string) {
  const session = s.sessions.find(v => v.id === sid && !v.closed);
  if (!session) reject("This dining session has ended");
  return session;
}
function sessionAccess(s: State, actor: Actor, sid: string): void {
  active(s, sid);
  if (actor.role === "guest" && actor.session_id !== sid) reject("This table session is not yours");
}
export async function initEngine(_bytes?: BufferSource): Promise<void> {
  // Browser engine is ordinary TypeScript; no WASM or Rust runtime required.
}
export function bill(state: State, session_id: string): Bill {
  const subtotal = state.orders.filter(o => o.session_id === session_id && o.status !== "pending" && o.status !== "rejected")
    .flatMap(o => o.lines).reduce((total,l) => total + l.price * l.quantity, 0);
  const tax = Math.floor((subtotal * state.restaurant.tax_bps + 5000)/10000);
  const service = Math.floor((subtotal * state.restaurant.service_bps + 5000)/10000);
  const paid = state.payments.filter(p => p.session_id === session_id).reduce((total,p) => total + p.amount, 0);
  const total = subtotal + tax + service;
  return {subtotal,tax,service,total,paid,balance:total-paid};
}
export function execute(state: State, actor: Actor, command: Command): State {
  if (typeof command.key !== "string" || command.key.length < 8 || command.key.length > 128) reject("A valid retry key is required");
  if (typeof command.now !== "string" || command.now.length < 10 || command.now.length > 40) reject("Invalid timestamp");
  const s = structuredClone(state);
  const d: Record<string, any> = command.data && typeof command.data === "object" && !Array.isArray(command.data) ? command.data as Record<string,any> : {};
  const op = command.op;
  if (op === "open_session") {
    permit(actor, "owner", "waiter");
    const tableId = field(d,"table_id");
    const table = s.tables.find(t => t.id === tableId);
    if (!table) reject("Table not found");
    if (table.dirty) reject("Mark this table clean before seating guests");
    if (s.sessions.some(v => v.table_id === tableId && !v.closed)) reject("This table already has an active visit");
    const guests = integer(d,"guests",1,table.seats);
    const token = field(d,"token");
    if (token.length < 32 || s.sessions.some(v => v.token === token)) reject("Use a fresh, secure session token");
    s.sessions.push({id:nextId(s,"visit"),table_id:tableId,token,guests,opened:command.now,closed:false});
  } else if (op === "submit_order") {
    permit(actor,"owner","waiter","guest");
    const sid = field(d,"session_id");
    sessionAccess(s,actor,sid);
    if (s.orders.some(o=>o.session_id===sid&&o.key===command.key)) return s;
    if (!Array.isArray(d.lines)) reject("No items selected");
    if (d.lines.length < 1 || d.lines.length > 50) reject("Choose between 1 and 50 items");
    const lines = d.lines.map((input:any)=>{
      if (!input || typeof input !== "object") reject("Invalid item");
      const itemId = field(input,"item_id");
      const item = s.menu.find(i=>i.id===itemId&&i.available);
      if (!item) reject("An item is no longer available; review your cart");
      const quantity = integer(input,"quantity",1,30);
      return {item_id:itemId,name:item.name,quantity,price:item.price,status:"queued"};
    });
    const note = typeof d.note === "string" ? d.note : "";
    if (new TextEncoder().encode(note).length > 500) reject("Note is too long");
    const guest = actor.role === "guest";
    s.orders.push({id:nextId(s,"order"),session_id:sid,status:guest?"pending":"accepted",source:guest?"QR menu":"Staff",lines,note,created:command.now,key:command.key});
  } else if (op === "review_order") {
    permit(actor,"owner","waiter");
    const order = s.orders.find(o=>o.id===field(d,"order_id"));
    if (!order) reject("Order not found");
    if (typeof d.accept !== "boolean") reject("Choose accept or reject");
    if (d.accept && order.lines.some(l=>!s.menu.some(i=>i.id===l.item_id&&i.available))) reject("An item is now unavailable; decline this request and help the guest reorder");
    if (order.status !== "pending") reject("This order has already been reviewed");
    order.status = d.accept?"accepted":"rejected";
  } else if (op === "advance_line") {
    permit(actor,"owner","kitchen","waiter");
    const order = s.orders.find(o=>o.id===field(d,"order_id"));
    if (!order) reject("Order not found");
    const index = integer(d,"index",0,49);
    if (!["accepted","preparing","ready"].includes(order.status)) reject("Only accepted kitchen tickets can progress");
    const line = order.lines[index];
    if (!line) reject("Item not found");
    if (line.status !== field(d,"expected_status")) reject("This item has already moved on. Refresh the kitchen before trying again");
    if (line.status === "queued" || line.status === "preparing") {
      permit(actor,"owner","kitchen");
      line.status = line.status === "queued" ? "preparing" : "ready";
    } else if (line.status === "ready") {
      permit(actor,"owner","waiter");
      line.status = "served";
    } else reject("This item is already served");
    order.status = order.lines.every(l=>l.status==="served")?"served":order.lines.every(l=>["ready","served"].includes(l.status))?"ready":"preparing";
  } else if (op === "pay") {
    permit(actor,"owner","cashier");
    const sid = field(d,"session_id");
    active(s,sid);
    if (s.payments.some(p=>p.session_id===sid&&p.key===command.key)) return s;
    if (s.orders.some(o=>o.session_id===sid&&o.status==="pending")) reject("Review pending orders before taking payment");
    const amount = integer(d,"amount",1,100000000);
    if (amount > bill(s,sid).balance) reject("Payment exceeds the remaining balance");
    const method = field(d,"method");
    if (method !== "cash") reject("Online payments are not connected; only received cash can be recorded");
    s.payments.push({id:nextId(s,"payment"),session_id:sid,amount,method,key:command.key,created:command.now});
  } else if (op === "close_session") {
    permit(actor,"owner","cashier");
    const sid = field(d,"session_id");
    const session = active(s,sid);
    if (bill(s,sid).balance !== 0) reject("Settle the balance before closing this visit");
    if (s.orders.some(o=>o.session_id===sid&&!["served","rejected"].includes(o.status))) reject("Complete or reject all orders before closing");
    session.closed = true;
    const table = s.tables.find(t=>t.id===session.table_id)!;
    table.dirty = true;
    s.requests.filter(r=>r.session_id===sid).forEach(r=>r.resolved=true);
  } else if (op === "clean_table") {
    permit(actor,"owner","waiter");
    const table = s.tables.find(t=>t.id===field(d,"table_id"));
    if (!table) reject("Table not found");
    table.dirty = false;
  } else if (op === "service_request") {
    permit(actor,"owner","waiter","guest");
    const sid = field(d,"session_id");
    sessionAccess(s,actor,sid);
    const kind = field(d,"kind");
    if (!["waiter","bill"].includes(kind)) reject("Unknown service request");
    if (s.requests.some(r=>r.session_id===sid&&r.kind===kind&&!r.resolved)) return s;
    s.requests.push({id:nextId(s,"request"),session_id:sid,kind,resolved:false,created:command.now});
  } else if (op === "resolve_request") {
    permit(actor,"owner","waiter","cashier");
    const request = s.requests.find(r=>r.id===field(d,"request_id"));
    if (!request) reject("Request not found");
    request.resolved = true;
  } else if (op === "save_menu_item") {
    permit(actor,"owner");
    const keys=["id","name","description","category","price","available","image","dietary"] as const;
    if (!keys.every(k=>Object.hasOwn(d,k))||!["id","name","description","category","image","dietary"].every(k=>typeof d[k]==="string")||typeof d.available!=="boolean"||typeof d.price!=="number"||!Number.isInteger(d.price)) reject("Complete all menu fields");
    const item=Object.fromEntries(keys.map(k=>[k,d[k]])) as unknown as State["menu"][number];
    item.name=item.name.trim();
    item.category=item.category.trim();
    if (!item.name||item.name.length>100||!item.category||item.category.length>60||item.price<1||item.price>10000000||item.description.length>500) reject("Check the item name, category, description and price");
    if (!["momo","bowl","curry","salad","drink","dessert"].includes(item.image)) reject("Choose a supported photo");
    if (!item.id){item.id=nextId(s,"dish");s.menu.push(item);}
    else {
      const index=s.menu.findIndex(i=>i.id===item.id);
      if(index===-1)reject("Menu item not found");
      s.menu[index]=item;
    }
  } else if (op === "update_restaurant") {
    permit(actor,"owner");
    const name=field(d,"name"),tagline=field(d,"tagline"),address=field(d,"address");
    const tax_bps=integer(d,"tax_bps",0,3000),service_bps=integer(d,"service_bps",0,2000);
    if((tax_bps!==s.restaurant.tax_bps||service_bps!==s.restaurant.service_bps)&&s.sessions.some(v=>!v.closed))reject("Close active visits before changing billing rates");
    Object.assign(s.restaurant,{name,tagline,address,tax_bps,service_bps});
  } else if (op === "adjust_stock") {
    permit(actor,"owner");
    const stock=s.stock.find(i=>i.id===field(d,"stock_id"));
    if(!stock)reject("Stock item not found");
    const delta=integer(d,"delta",-100000,100000);
    if(field(d,"reason").length<3)reject("Please describe the stock adjustment");
    if(stock.quantity+delta<0)reject("Stock cannot fall below zero");
    stock.quantity+=delta;
  } else reject("Unknown action");
  s.version++;
  s.audit.push({id:nextId(s,"event"),actor:actor.name,action:op+" · "+JSON.stringify(d),created:command.now});
  return s;
}
