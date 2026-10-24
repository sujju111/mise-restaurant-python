import type { Actor, Bill, Command, State } from "./types";
type EngineExports = WebAssembly.Exports & {
  memory: WebAssembly.Memory;
  allocate: (len: number) => number;
  release: (ptr: number, len: number) => void;
  run: (ptr: number, len: number) => bigint;
};
let exports: EngineExports;
export async function initEngine(bytes?: BufferSource) {
  const input =
    bytes ??
    (await (
      await fetch(`${import.meta.env.BASE_URL}engine/mise_core.wasm`)
    ).arrayBuffer());
  const result = await WebAssembly.instantiate(input, {});
  exports = result.instance.exports as EngineExports;
}
function invoke<T>(input: unknown): T {
  if (!exports)
    throw new Error("Restaurant engine has not loaded. Please reload.");
  const bytes = new TextEncoder().encode(JSON.stringify(input));
  const p = exports.allocate(bytes.length);
  let out = 0,
    len = 0;
  try {
    new Uint8Array(exports.memory.buffer, p, bytes.length).set(bytes);
    const packed = exports.run(p, bytes.length);
    out = Number(packed & 0xffffffffn);
    len = Number(packed >> 32n);
    const response = JSON.parse(
      new TextDecoder().decode(new Uint8Array(exports.memory.buffer, out, len)),
    );
    if (!response.ok) throw new Error(response.error);
    return response.result;
  } finally {
    exports.release(p, bytes.length);
    if (out) exports.release(out, len);
  }
}
export function execute(state: State, actor: Actor, command: Command): State {
  return invoke<{ state: State }>({ state, actor, command }).state;
}
export function bill(state: State, session_id: string): Bill {
  return invoke<{ bill: Bill }>({ state, action: "bill", session_id }).bill;
}
