export type Role = "owner" | "waiter" | "kitchen" | "cashier" | "guest";
export interface Restaurant {
  id: string;
  slug: string;
  name: string;
  tagline: string;
  address: string;
  tax_bps: number;
  service_bps: number;
}
export interface Dish {
  id: string;
  name: string;
  description: string;
  category: string;
  price: number;
  available: boolean;
  image: string;
  dietary: string;
}
export interface DiningTable {
  id: string;
  name: string;
  seats: number;
  section: string;
  dirty: boolean;
}
export interface Session {
  id: string;
  table_id: string;
  token: string;
  guests: number;
  opened: string;
  closed: boolean;
}
export interface Line {
  item_id: string;
  name: string;
  quantity: number;
  price: number;
  status: string;
}
export interface Order {
  id: string;
  session_id: string;
  status: string;
  source: string;
  lines: Line[];
  note: string;
  created: string;
  key: string;
}
export interface Payment {
  id: string;
  session_id: string;
  amount: number;
  method: string;
  key: string;
  created: string;
}
export interface ServiceRequest {
  id: string;
  session_id: string;
  kind: string;
  resolved: boolean;
  created: string;
}
export interface Stock {
  id: string;
  name: string;
  unit: string;
  quantity: number;
  threshold: number;
}
export interface Audit {
  id: string;
  actor: string;
  action: string;
  created: string;
}
export interface State {
  schema: number;
  version: number;
  sequence: number;
  restaurant: Restaurant;
  menu: Dish[];
  tables: DiningTable[];
  sessions: Session[];
  orders: Order[];
  payments: Payment[];
  requests: ServiceRequest[];
  stock: Stock[];
  audit: Audit[];
}
export interface Bill {
  subtotal: number;
  tax: number;
  service: number;
  total: number;
  paid: number;
  balance: number;
}
export interface Actor {
  role: Role;
  name: string;
  session_id?: string;
}
export interface Command {
  op: string;
  data: unknown;
  key: string;
  now: string;
}
export type CartLine = { item_id: string; quantity: number };
