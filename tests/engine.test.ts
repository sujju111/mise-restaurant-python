import { beforeAll, describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { initEngine, execute, bill } from "../src/engine";
import seed from "../crates/core/src/seed.json";
import type { State, Command } from "../src/types";
beforeAll(() => initEngine(readFileSync("public/engine/mise_core.wasm")));
const owner = { role: "owner" as const, name: "Owner" };
const cmd = (op: string, data: unknown, key = "test-key-1234"): Command => ({
  op,
  data,
  key,
  now: "2026-10-24T12:00:00Z",
});
describe("shipped Rust WebAssembly engine", () => {
  it("executes the real guest approval and settlement rules in the browser artifact", () => {
    let s = execute(
      structuredClone(seed) as State,
      owner,
      cmd("open_session", {
        table_id: "table-1",
        guests: 2,
        token: "a-secure-guest-token-1234567890123456",
      }),
    );
    const sid = s.sessions[0].id;
    const guest = { role: "guest" as const, name: "Guest", session_id: sid };
    const order = cmd("submit_order", {
      session_id: sid,
      lines: [{ item_id: "dish-1", quantity: 2, price: 1 }],
    });
    s = execute(s, guest, order);
    s = execute(s, guest, order);
    expect(s.orders).toHaveLength(1);
    expect(bill(s, sid).total).toBe(0);
    s = execute(
      s,
      owner,
      cmd("review_order", { order_id: s.orders[0].id, accept: true }),
    );
    expect(bill(s, sid).total).toBe(64000);
    expect(() =>
      execute(
        s,
        guest,
        cmd("pay", { session_id: sid, amount: 64000, method: "cash" }),
      ),
    ).toThrow("Your role");
    s = execute(
      s,
      owner,
      cmd("pay", { session_id: sid, amount: 64000, method: "cash" }),
    );
    expect(bill(s, sid).balance).toBe(0);
  });
  it("keeps the saved state untouched after an invalid action", () => {
    const s = structuredClone(seed) as State;
    expect(() =>
      execute(
        s,
        owner,
        cmd("open_session", {
          table_id: "missing",
          guests: 2,
          token: "secure-token-1234567890123456789012",
        }),
      ),
    ).toThrow();
    expect(s.sessions).toEqual([]);
  });
});
