"""Python port of the Mise restaurant state-transition and billing rules.

All monetary values are integer minor units (paisa). An invalid command
raises DomainError without modifying the input state.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any
import json

State = dict[str, Any]

class DomainError(ValueError):
    """Business command rejected."""


def fail(message: str) -> None:
    raise DomainError(message)


def field(value: dict, name: str) -> str:
    value = value.get(name)
    if not isinstance(value, str):
        fail(f"Missing {name}")
    value = value.strip()
    if not value or len(value.encode()) > 500:
        fail(f"Invalid {name}")
    return value


def integer(value: dict, name: str, low: int, high: int) -> int:
    number = value.get(name)
    if type(number) is not int:
        fail(f"Invalid {name}")
    if not low <= number <= high:
        fail(f"{name} must be between {low} and {high}")
    return number


def permit(actor: dict, *roles: str) -> None:
    if actor.get("role") not in roles:
        fail("Your role cannot perform this action")


def find(rows: list[dict], key: str, value: Any, message: str) -> dict:
    result = next((row for row in rows if row.get(key) == value), None)
    if result is None:
        fail(message)
    return result


def next_id(s: State, prefix: str) -> str:
    s["sequence"] += 1
    return f'{prefix}-{s["sequence"]}'


def active_session(s: State, sid: str) -> dict:
    session = next((v for v in s["sessions"] if v["id"] == sid and not v["closed"]), None)
    if session is None:
        fail("This dining session has ended")
    return session


def session_access(s: State, actor: dict, sid: str) -> None:
    active_session(s, sid)
    if actor.get("role") == "guest" and actor.get("session_id") != sid:
        fail("This table session is not yours")


def bill(s: State, sid: str) -> dict[str, int]:
    subtotal = sum(line["price"] * line["quantity"] for order in s["orders"] if order["session_id"] == sid and order["status"] not in ("pending", "rejected") for line in order["lines"])
    tax = (subtotal * s["restaurant"]["tax_bps"] + 5000) // 10000
    service = (subtotal * s["restaurant"]["service_bps"] + 5000) // 10000
    paid = sum(p["amount"] for p in s["payments"] if p["session_id"] == sid)
    total = subtotal + tax + service
    return dict(subtotal=subtotal, tax=tax, service=service, total=total, paid=paid, balance=total-paid)


def execute(state: State, actor: dict, command: dict) -> State:
    key, now = command.get("key"), command.get("now")
    if not isinstance(key, str) or not 8 <= len(key.encode()) <= 128:
        fail("A valid retry key is required")
    if not isinstance(now, str) or not 10 <= len(now.encode()) <= 40:
        fail("Invalid timestamp")
    s = deepcopy(state)
    d = command.get("data")
    if not isinstance(d, dict):
        d = {}
    op = command.get("op")
    if op == "open_session":
        permit(actor, "owner", "waiter")
        table_id = field(d, "table_id")
        table = find(s["tables"], "id", table_id, "Table not found")
        if table["dirty"]:
            fail("Mark this table clean before seating guests")
        if any(v["table_id"] == table_id and not v["closed"] for v in s["sessions"]):
            fail("This table already has an active visit")
        guests = integer(d, "guests", 1, table["seats"])
        token = field(d, "token")
        if len(token.encode()) < 32 or any(v["token"] == token for v in s["sessions"]):
            fail("Use a fresh, secure session token")
        s["sessions"].append(dict(id=next_id(s, "visit"), table_id=table_id, token=token, guests=guests, opened=now, closed=False))
    elif op == "submit_order":
        permit(actor, "owner", "waiter", "guest")
        sid = field(d, "session_id")
        session_access(s, actor, sid)
        if any(o["session_id"] == sid and o["key"] == key for o in s["orders"]):
            return s
        requested = d.get("lines")
        if not isinstance(requested, list):
            fail("No items selected")
        if not 1 <= len(requested) <= 50:
            fail("Choose between 1 and 50 items")
        lines = []
        for item in requested:
            if not isinstance(item, dict):
                fail("Invalid item")
            item_id = field(item, "item_id")
            menu_item = next((i for i in s["menu"] if i["id"] == item_id and i["available"]), None)
            if menu_item is None:
                fail("An item is no longer available; review your cart")
            qty = integer(item, "quantity", 1, 30)
            lines.append(dict(item_id=item_id, name=menu_item["name"], quantity=qty, price=menu_item["price"], status="queued"))
        note = d.get("note") if isinstance(d.get("note"), str) else ""
        if len(note.encode()) > 500:
            fail("Note is too long")
        guest = actor["role"] == "guest"
        s["orders"].append(dict(id=next_id(s, "order"), session_id=sid, status="pending" if guest else "accepted", source="QR menu" if guest else "Staff", lines=lines, note=note, created=now, key=key))
    elif op == "review_order":
        permit(actor, "owner", "waiter")
        order = find(s["orders"], "id", field(d, "order_id"), "Order not found")
        accept = d.get("accept")
        if not isinstance(accept, bool):
            fail("Choose accept or reject")
        if accept and any(not any(i["id"] == l["item_id"] and i["available"] for i in s["menu"]) for l in order["lines"]):
            fail("An item is now unavailable; decline this request and help the guest reorder")
        if order["status"] != "pending":
            fail("This order has already been reviewed")
        order["status"] = "accepted" if accept else "rejected"
    elif op == "advance_line":
        permit(actor, "owner", "kitchen", "waiter")
        order = find(s["orders"], "id", field(d, "order_id"), "Order not found")
        idx = integer(d, "index", 0, 49)
        if order["status"] not in ("accepted", "preparing", "ready"):
            fail("Only accepted kitchen tickets can progress")
        if idx >= len(order["lines"]):
            fail("Item not found")
        line = order["lines"][idx]
        if line["status"] != field(d, "expected_status"):
            fail("This item has already moved on. Refresh the kitchen before trying again")
        if line["status"] in ("queued", "preparing"):
            permit(actor, "owner", "kitchen")
            line["status"] = "preparing" if line["status"] == "queued" else "ready"
        elif line["status"] == "ready":
            permit(actor, "owner", "waiter")
            line["status"] = "served"
        else:
            fail("This item is already served")
        statuses = [x["status"] for x in order["lines"]]
        order["status"] = "served" if all(x == "served" for x in statuses) else "ready" if all(x in ("ready", "served") for x in statuses) else "preparing"
    elif op == "pay":
        permit(actor, "owner", "cashier")
        sid = field(d, "session_id")
        active_session(s, sid)
        if any(p["session_id"] == sid and p["key"] == key for p in s["payments"]):
            return s
        if any(o["session_id"] == sid and o["status"] == "pending" for o in s["orders"]):
            fail("Review pending orders before taking payment")
        amount = integer(d, "amount", 1, 100_000_000)
        if amount > bill(s, sid)["balance"]:
            fail("Payment exceeds the remaining balance")
        method = field(d, "method")
        if method != "cash":
            fail("Online payments are not connected; only received cash can be recorded")
        s["payments"].append(dict(id=next_id(s, "payment"), session_id=sid, amount=amount, method=method, key=key, created=now))
    elif op == "close_session":
        permit(actor, "owner", "cashier")
        sid = field(d, "session_id")
        session = active_session(s, sid)
        if bill(s, sid)["balance"] != 0:
            fail("Settle the balance before closing this visit")
        if any(o["session_id"] == sid and o["status"] not in ("served", "rejected") for o in s["orders"]):
            fail("Complete or reject all orders before closing")
        session["closed"] = True
        find(s["tables"], "id", session["table_id"], "Table not found")["dirty"] = True
        for request in s["requests"]:
            if request["session_id"] == sid:
                request["resolved"] = True
    elif op == "clean_table":
        permit(actor, "owner", "waiter")
        find(s["tables"], "id", field(d, "table_id"), "Table not found")["dirty"] = False
    elif op == "service_request":
        permit(actor, "owner", "waiter", "guest")
        sid = field(d, "session_id")
        session_access(s, actor, sid)
        kind = field(d, "kind")
        if kind not in ("waiter", "bill"):
            fail("Unknown service request")
        if any(r["session_id"] == sid and r["kind"] == kind and not r["resolved"] for r in s["requests"]):
            return s
        s["requests"].append(dict(id=next_id(s, "request"), session_id=sid, kind=kind, resolved=False, created=now))
    elif op == "resolve_request":
        permit(actor, "owner", "waiter", "cashier")
        find(s["requests"], "id", field(d, "request_id"), "Request not found")["resolved"] = True
    elif op == "save_menu_item":
        permit(actor, "owner")
        required = ("id", "name", "description", "category", "price", "available", "image", "dietary")
        if any(k not in d for k in required) or not all(isinstance(d[k], str) for k in ("id", "name", "description", "category", "image", "dietary")) or not isinstance(d["available"], bool) or type(d["price"]) is not int:
            fail("Complete all menu fields")
        item = {k: d[k] for k in required}
        item["name"] = item["name"].strip()
        item["category"] = item["category"].strip()
        if not item["name"] or len(item["name"].encode()) > 100 or not item["category"] or len(item["category"].encode()) > 60 or not 1 <= item["price"] <= 10_000_000 or len(item["description"].encode()) > 500:
            fail("Check the item name, category, description and price")
        if item["image"] not in ("momo", "bowl", "curry", "salad", "drink", "dessert"):
            fail("Choose a supported photo")
        if not item["id"]:
            item["id"] = next_id(s, "dish")
            s["menu"].append(item)
        else:
            find(s["menu"], "id", item["id"], "Menu item not found").update(item)
    elif op == "update_restaurant":
        permit(actor, "owner")
        name, tagline, address = field(d, "name"), field(d, "tagline"), field(d, "address")
        tax = integer(d, "tax_bps", 0, 3000)
        service = integer(d, "service_bps", 0, 2000)
        if (tax != s["restaurant"]["tax_bps"] or service != s["restaurant"]["service_bps"]) and any(not v["closed"] for v in s["sessions"]):
            fail("Close active visits before changing billing rates")
        s["restaurant"].update(name=name, tagline=tagline, address=address, tax_bps=tax, service_bps=service)
    elif op == "adjust_stock":
        permit(actor, "owner")
        stock = find(s["stock"], "id", field(d, "stock_id"), "Stock item not found")
        delta = integer(d, "delta", -100_000, 100_000)
        reason = field(d, "reason")
        if len(reason.encode()) < 3:
            fail("Please describe the stock adjustment")
        if stock["quantity"] + delta < 0:
            fail("Stock cannot fall below zero")
        stock["quantity"] += delta
    else:
        fail("Unknown action")
    s["version"] += 1
    s["audit"].append(dict(id=next_id(s, "event"), actor=actor["name"], action=f'{op} · {json.dumps(d, ensure_ascii=False, separators=(",", ":"))}', created=now))
    return s


def guest_view(s: State, token: str) -> dict:
    session = next((v for v in s["sessions"] if v["token"] == token and not v["closed"]), None)
    if session is None:
        fail("This table link has expired. Ask your waiter for the current QR code.")
    sid = session["id"]
    return dict(restaurant=s["restaurant"], menu=s["menu"], session={k: session[k] for k in ("id", "table_id", "guests")}, orders=[{k: o[k] for k in ("id", "status", "lines", "note", "created")} for o in s["orders"] if o["session_id"] == sid], bill=bill(s, sid), requests=[r for r in s["requests"] if r["session_id"] == sid])
