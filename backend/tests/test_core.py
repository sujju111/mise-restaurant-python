import json
from copy import deepcopy
from pathlib import Path
import pytest
from mise.core import execute, bill, guest_view, DomainError

SEED = json.loads((Path(__file__).parents[1] / "mise" / "seed.json").read_text())
OWNER = {"role": "owner", "name": "Owner"}
def guest(sid): return {"role": "guest", "name": "Guest", "session_id": sid}
def cmd(op, data, key="retry-key-1234"): return {"op":op, "data":data, "key":key, "now":"2026-10-24T12:00:00Z"}
def opened():
    s = execute(SEED, OWNER, cmd("open_session", {"table_id":"table-1", "guests":2, "token":"secure-guest-session-token-1234567890"}))
    return s, s["sessions"][0]["id"]
def order(s, role="guest", key="order-key-1234"):
    sid = s["sessions"][0]["id"]
    return execute(s, guest(sid) if role=="guest" else OWNER, cmd("submit_order", {"session_id":sid, "lines":[{"item_id":"dish-1", "quantity":2, "price":1}]}, key))

def test_client_price_never_overrides_menu_price():
    s,sid=opened()
    s=order(s)
    assert s["orders"][0]["status"]=="pending"
    assert s["orders"][0]["lines"][0]["price"]==32000
    assert bill(s,sid)["total"]==0
    s=execute(s,OWNER,cmd("review_order",{"order_id":s["orders"][0]["id"],"accept":True}))
    assert bill(s,sid)["total"]==64000

def test_duplicate_order_and_cash_are_idempotent():
    s,sid=opened()
    s=order(s,"owner")
    assert order(s,"owner")==s
    paycmd=cmd("pay",{"session_id":sid,"amount":64000,"method":"cash"},"cash-key-1234")
    s=execute(s,OWNER,paycmd)
    assert execute(s,OWNER,paycmd)==s
    assert len(s["payments"])==1
    assert bill(s,sid)["balance"]==0

def test_guest_cannot_read_or_mutate_another_visit():
    s,sid=opened()
    with pytest.raises(DomainError): guest_view(s,"other")
    with pytest.raises(DomainError): execute(s,guest("other"),cmd("submit_order",{"session_id":sid,"lines":[{"item_id":"dish-1","quantity":1}]}))

def test_payment_and_kitchen_status_gate():
    s,sid=opened()
    s=order(s)
    with pytest.raises(DomainError): execute(s,OWNER,cmd("pay",{"session_id":sid,"amount":10,"method":"cash"}))
    with pytest.raises(DomainError): execute(s,OWNER,cmd("advance_line",{"order_id":s["orders"][0]["id"],"index":0,"expected_status":"queued"}))
    with pytest.raises(DomainError): execute(s,guest(sid),cmd("review_order",{"order_id":s["orders"][0]["id"],"accept":True}))

def test_reject_bad_menu_and_payment_permissions():
    s,sid=opened()
    s=order(s,"owner")
    with pytest.raises(DomainError): execute(s,{"role":"waiter","name":"Waiter"},cmd("save_menu_item",s["menu"][0]))
    with pytest.raises(DomainError): execute(s,{"role":"waiter","name":"Waiter"},cmd("pay",{"session_id":sid,"amount":1,"method":"cash"}))
    with pytest.raises(DomainError): execute(s,OWNER,cmd("pay",{"session_id":sid,"amount":64000,"method":"online"}))
    with pytest.raises(DomainError): execute(s,OWNER,cmd("pay",{"session_id":sid,"amount":64001,"method":"cash"}))

def test_failed_transactions_leave_original_untouched():
    s,sid=opened()
    before=deepcopy(s)
    with pytest.raises(DomainError): execute(s,OWNER,cmd("update_restaurant",{"name":"Renamed","tagline":"Tagline","address":"Address","tax_bps":1300,"service_bps":0}))
    assert s==before
    with pytest.raises(DomainError): execute(s,OWNER,cmd("submit_order",{"session_id":sid,"lines":[{"item_id":"dish-1","quantity":-1}]}))
    assert s==before

def test_session_closes_after_full_service_and_payment():
    s,sid=opened()
    s=order(s,"owner")
    for status in ("queued","preparing","ready"):
        s=execute(s,OWNER,cmd("advance_line",{"order_id":s["orders"][0]["id"],"index":0,"expected_status":status},"advance-"+status))
    assert s["orders"][0]["status"]=="served"
    with pytest.raises(DomainError): execute(s,OWNER,cmd("close_session",{"session_id":sid}))
    s=execute(s,OWNER,cmd("pay",{"session_id":sid,"amount":64000,"method":"cash"}))
    token=s["sessions"][0]["token"]
    s=execute(s,OWNER,cmd("close_session",{"session_id":sid}))
    assert s["tables"][0]["dirty"] and s["sessions"][0]["closed"]
    with pytest.raises(DomainError): guest_view(s,token)

def test_coalesced_service_requests_and_rejection():
    s,sid=opened()
    c=cmd("service_request",{"session_id":sid,"kind":"bill"})
    s=execute(s,guest(sid),c)
    assert execute(s,guest(sid),c)==s
    s=order(s)
    s=execute(s,OWNER,cmd("review_order",{"order_id":s["orders"][0]["id"],"accept":False}))
    assert bill(s,sid)["total"]==0

def test_rates_use_integer_half_up_rounding():
    seed=deepcopy(SEED)
    seed["restaurant"]["tax_bps"]=1300
    seed["restaurant"]["service_bps"]=1000
    seed["menu"][0]["price"]=101
    s=execute(seed,OWNER,cmd("open_session",{"table_id":"table-1","guests":1,"token":"secure-guest-session-token-1234567890"}))
    s=order(s,"owner")
    assert bill(s,s["sessions"][0]["id"])==dict(subtotal=202,tax=26,service=20,total=248,paid=0,balance=248)

def test_stale_kitchen_tap_and_unavailable_menu():
    s,sid=opened()
    s=order(s,"owner")
    action=cmd("advance_line",{"order_id":s["orders"][0]["id"],"index":0,"expected_status":"queued"})
    s=execute(s,OWNER,action)
    with pytest.raises(DomainError): execute(s,OWNER,action)
    s,sid=opened()
    s=order(s)
    changed=deepcopy(s)
    changed["menu"][0]["available"]=False
    with pytest.raises(DomainError): execute(changed,OWNER,cmd("review_order",{"order_id":changed["orders"][0]["id"],"accept":True}))

def test_stock_adjustment_and_menu_edit():
    s=execute(SEED,OWNER,cmd("adjust_stock",{"stock_id":"rice","delta":-2,"reason":"Inventory correction"}))
    assert s["stock"][0]["quantity"]==26
    s=execute(s,OWNER,cmd("save_menu_item",dict(id="",name="Extra dish",description="Description",category="Specials",price=12300,available=True,image="momo",dietary="")))
    assert s["menu"][-1]["name"]=="Extra dish"
