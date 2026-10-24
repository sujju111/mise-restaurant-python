"""Generate strong development credentials in ignored .env.local."""
from pathlib import Path
from secrets import token_urlsafe
import json
root = Path(__file__).resolve().parents[1]
output = root / ".env.local"
if output.exists():
    raise SystemExit(f"{output} exists; leaving credentials unchanged")
accounts = [dict(token=token_urlsafe(36), tenant=t, role=r, name=f"{t.title()} {r.title()}") for t in ("juniper", "ember") for r in ("owner", "waiter", "kitchen", "cashier")]
output.write_text("MISE_ACCOUNTS='" + json.dumps(accounts, separators=(",", ":")) + "'\nMISE_DATABASE=mise.sqlite\n", encoding="utf-8")
print(f"Wrote {output}. Keep this file secret. Owner tokens:")
for a in accounts:
    if a["role"] == "owner":
        print(f'  {a["tenant"]}: {a["token"]}')
