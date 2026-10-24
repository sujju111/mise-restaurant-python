"""FastAPI replacement for the Rust/Axum Mise restaurant API.

Keeps the original endpoint paths, tenant-scoped SQLite storage,
staff authorization, guest visit tokens and JSON response shapes.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from secrets import compare_digest, token_urlsafe
from threading import RLock
from time import monotonic
from typing import Any
import json
import os
import sqlite3

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .core import DomainError, execute, guest_view

EXPIRED = "This table link has expired. Ask your waiter for a new QR."
DATABASE_ERROR = "The server could not save this action. Retry with the same key."
SEED_PATH = Path(__file__).with_name("seed.json")


class Command(BaseModel):
    op: str
    data: dict[str, Any] = Field(default_factory=dict)
    key: str
    now: str


def make_tenant(seed: dict, tenant: str) -> dict:
    seed = json.loads(json.dumps(seed))
    if tenant == "ember":
        seed["restaurant"].update(id="ember", slug="ember-kitchen", name="Ember Kitchen", tagline="Made over fire. Shared with friends.", address="Lazimpat, Kathmandu")
        seed["menu"] = seed["menu"][:6]
    for table in seed["tables"]:
        table["dirty"] = False
    return seed


class Database:
    def __init__(self, path: str, accounts: list[dict], seed: dict):
        self.lock = RLock()
        self.accounts = accounts
        self.conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None, timeout=10)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("CREATE TABLE IF NOT EXISTS workspaces (tenant TEXT PRIMARY KEY, body TEXT NOT NULL)")
        with self.lock, self.conn:
            for tenant in ("juniper", "ember"):
                self.conn.execute("INSERT OR IGNORE INTO workspaces (tenant, body) VALUES (?, ?)", (tenant, json.dumps(make_tenant(seed, tenant))))

    def close(self):
        self.conn.close()

    def load(self, tenant: str) -> dict:
        row = self.conn.execute("SELECT body FROM workspaces WHERE tenant=?", (tenant,)).fetchone()
        if row is None:
            raise HTTPException(404, detail="Restaurant not found")
        return json.loads(row[0])

    def apply(self, tenant: str, actor: dict, command: dict) -> dict:
        with self.lock:
            try:
                self.conn.execute("BEGIN IMMEDIATE")
                current = self.load(tenant)
                result = execute(current, actor, command)
                self.conn.execute("UPDATE workspaces SET body=? WHERE tenant=?", (json.dumps(result), tenant))
                self.conn.execute("COMMIT")
                return result
            except BaseException:
                if self.conn.in_transaction:
                    self.conn.execute("ROLLBACK")
                raise


def parse_accounts(raw: str) -> list[dict]:
    try:
        records = json.loads(raw)
    except (ValueError, TypeError) as error:
        raise RuntimeError("MISE_ACCOUNTS must contain valid JSON") from error
    if not isinstance(records, list) or not records:
        raise RuntimeError("Set MISE_ACCOUNTS to a nonempty staff account array")
    tokens = []
    for account in records:
        if not isinstance(account, dict) or not all(isinstance(account.get(k), str) for k in ("token", "tenant", "role", "name")):
            raise RuntimeError("Each account must have token, tenant, role, name")
        if len(account["token"]) < 32 or account["role"] not in ("owner", "waiter", "kitchen", "cashier") or account["tenant"] not in ("juniper", "ember"):
            raise RuntimeError("Use 32+ character tokens, valid roles and supported tenants")
        if any(compare_digest(account["token"], token) for token in tokens):
            raise RuntimeError("Staff tokens must be unique")
        tokens.append(account["token"])
    return records


def staff_view(state: dict, role: str) -> dict:
    state = json.loads(json.dumps(state))
    if role != "owner":
        state["audit"] = []
        state["stock"] = []
    if role not in ("owner", "waiter"):
        for session in state["sessions"]:
            session["token"] = ""
    if role == "kitchen":
        state["payments"] = []
        state["requests"] = []
    return state


def fresh_time() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def make_app(database: str | None = None, accounts: list[dict] | None = None, seed: dict | None = None) -> FastAPI:
    if accounts is None:
        accounts = parse_accounts(os.environ.get("MISE_ACCOUNTS", ""))
    else:
        accounts = parse_accounts(json.dumps(accounts))
    if seed is None:
        seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    db = Database(database or os.environ.get("MISE_DATABASE", "mise.sqlite"), accounts, seed)
    origins = os.environ.get("MISE_ORIGINS", "http://localhost:5173,http://localhost:4173,capacitor://localhost,https://localhost").split(",")
    api = FastAPI(title="Mise Python API", version="1.0.0", docs_url=None, redoc_url=None)
    api.state.db = db
    api.add_middleware(CORSMiddleware, allow_origins=[s.strip() for s in origins if s.strip()], allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["authorization", "content-type"])
    guest_limits: dict[str, tuple[float, int]] = {}
    limit_lock = RLock()

    def account(auth: str | None) -> dict:
        token = auth.removeprefix("Bearer ") if auth and auth.startswith("Bearer ") else ""
        matched = next((a for a in accounts if compare_digest(a["token"], token)), None)
        if matched is None:
            raise HTTPException(401, detail="Sign in with a valid staff token")
        return matched

    def limited(token: str) -> None:
        with limit_lock:
            now = monotonic()
            for name in list(guest_limits):
                if now - guest_limits[name][0] >= 60:
                    del guest_limits[name]
            if len(guest_limits) > 10000:
                raise HTTPException(429, detail="Please wait a moment and retry.")
            start, count = guest_limits.get(token, (now, 0))
            if now - start >= 60:
                start, count = now, 0
            count += 1
            guest_limits[token] = start, count
            if count > 90:
                raise HTTPException(429, detail="Please wait a minute before trying again.")

    def find_guest(token: str) -> tuple[str, dict, dict]:
        if not 32 <= len(token) <= 128:
            raise HTTPException(404, detail=EXPIRED)
        with db.lock:
            for tenant in ("juniper", "ember"):
                state = db.load(tenant)
                session = next((x for x in state["sessions"] if not x["closed"] and compare_digest(x["token"], token)), None)
                if session:
                    return tenant, state, session
        raise HTTPException(404, detail=EXPIRED)

    @api.exception_handler(HTTPException)
    async def http_errors(_: Request, exc: HTTPException):
        return JSONResponse({"error": exc.detail}, status_code=exc.status_code)

    @api.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        return JSONResponse({"error": "Invalid command payload"}, status_code=422)

    @api.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError):
        return JSONResponse({"error": str(exc)}, status_code=422)

    @api.exception_handler(sqlite3.Error)
    async def database_error(_: Request, exc: sqlite3.Error):
        return JSONResponse({"error": DATABASE_ERROR}, status_code=500)

    @api.middleware("http")
    async def body_size(request: Request, call_next):
        if request.method == "POST":
            length = request.headers.get("content-length")
            if length and int(length) > 65536:
                return JSONResponse({"error": "Request too large"}, status_code=413)
            total, chunks = 0, []
            async for chunk in request.stream():
                total += len(chunk)
                if total > 65536:
                    return JSONResponse({"error": "Request too large"}, status_code=413)
                chunks.append(chunk)
            request._body = b"".join(chunks)
        return await call_next(request)

    @api.get("/health")
    def health():
        return {"status": "ok", "engine": "python"}

    @api.get("/api/me")
    def me(authorization: str | None = Header(None)):
        a = account(authorization)
        return {k: a[k] for k in ("name", "role", "tenant")}

    @api.get("/api/state")
    def state(authorization: str | None = Header(None)):
        a = account(authorization)
        with db.lock:
            return staff_view(db.load(a["tenant"]), a["role"])

    @api.post("/api/command")
    def staff_command(command: Command, authorization: str | None = Header(None)):
        a = account(authorization)
        cmd = command.model_dump()
        cmd["now"] = fresh_time()
        if cmd["op"] == "open_session":
            cmd["data"]["token"] = token_urlsafe(32)
        s = db.apply(a["tenant"], {"role": a["role"], "name": a["name"]}, cmd)
        return staff_view(s, a["role"])

    @api.get("/api/menu/{slug}")
    def menu(slug: str):
        with db.lock:
            for tenant in ("juniper", "ember"):
                s = db.load(tenant)
                if s["restaurant"]["slug"] == slug:
                    return {"restaurant": s["restaurant"], "menu": s["menu"]}
        raise HTTPException(404, detail="Restaurant menu not found")

    @api.get("/api/guest/{token}")
    def guest(token: str):
        limited(token)
        _, s, _ = find_guest(token)
        return guest_view(s, token)

    @api.post("/api/guest/{token}/command")
    def guest_command(token: str, command: Command):
        limited(token)
        tenant, _, session = find_guest(token)
        cmd = command.model_dump()
        if cmd["op"] not in ("submit_order", "service_request"):
            raise HTTPException(403, detail="Guests can only request service or submit an order")
        if cmd["data"].get("session_id") != session["id"]:
            raise HTTPException(403, detail="This table session is not yours")
        cmd["now"] = fresh_time()
        # Recheck visit validity under the same lock protecting SQLite writers.
        with db.lock:
            _, _, current_session = find_guest(token)
            if current_session["id"] != session["id"]:
                raise HTTPException(404, detail=EXPIRED)
            next_state = db.apply(tenant, {"role": "guest", "name": "QR guest", "session_id": session["id"]}, cmd)
        return guest_view(next_state, token)

    return api


def create_app():
    return make_app()


class LazyASGI:
    """Construct the app after Uvicorn loads credentials from .env.local."""
    def __init__(self):
        self.app = None
    async def __call__(self, scope, receive, send):
        if self.app is None:
            self.app = create_app()
        await self.app(scope, receive, send)

app = LazyASGI()
