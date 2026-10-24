import json
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from mise.api import make_app

ACCOUNTS=[
 {"token":"owner-juniper-token-1234567890123456","tenant":"juniper","role":"owner","name":"J Owner"},
 {"token":"owner-ember-token-123456789012345678","tenant":"ember","role":"owner","name":"E Owner"},
 {"token":"kitchen-juniper-token-12345678901234","tenant":"juniper","role":"kitchen","name":"Cook"},
]
SEED=json.loads((Path(__file__).parents[1]/"mise"/"seed.json").read_text())

@pytest.fixture
def client(tmp_path):
    api=make_app(str(tmp_path/"test.sqlite"),ACCOUNTS,SEED)
    with TestClient(api) as c: yield c
    api.state.db.close()
def auth(i=0): return {"Authorization":"Bearer "+ACCOUNTS[i]["token"]}
def command(op,data,key="test-key-12345"): return {"op":op,"data":data,"key":key,"now":"2026-10-24T12:00:00Z"}

def test_auth_tenants_and_public_menu(client):
    assert client.get("/api/state").status_code==401
    assert client.get("/api/me",headers=auth()).json()["tenant"]=="juniper"
    assert client.get("/api/state",headers=auth()).json()["restaurant"]["name"]=="Juniper House"
    assert client.get("/api/state",headers=auth(1)).json()["restaurant"]["name"]=="Ember Kitchen"
    assert len(client.get("/api/menu/ember-kitchen").json()["menu"])==6
    assert client.get("/api/menu/unknown").status_code==404
    assert client.get("/health").json()["engine"]=="python"

def test_guest_scope_and_trusted_pricing(client):
    s=client.post("/api/command",headers=auth(),json=command("open_session",{"table_id":"table-1","guests":2,"token":"ignored"})).json()
    session=s["sessions"][0]
    token=session["token"]
    assert len(token)>=32
    view=client.get("/api/guest/"+token).json()
    assert "payments" not in view and "audit" not in view and "token" not in view["session"]
    path="/api/guest/"+token+"/command"
    assert client.post(path,json=command("pay",{"session_id":session["id"],"amount":10,"method":"cash"})).status_code==403
    assert client.post(path,json=command("submit_order",{"session_id":"other","lines":[{"item_id":"dish-1","quantity":1}]})).status_code==403
    response=client.post(path,json=command("submit_order",{"session_id":session["id"],"lines":[{"item_id":"dish-1","quantity":1,"price":1}]}))
    assert response.status_code==200,response.text
    assert response.json()["orders"][0]["lines"][0]["price"]==32000

def test_kitchen_scope_and_failed_write(client):
    assert client.post("/api/command",headers=auth(2),json=command("update_restaurant",{"name":"No"})).status_code==422
    s=client.get("/api/state",headers=auth(2)).json()
    assert s["audit"]==[] and s["payments"]==[] and s["stock"]==[]
    assert client.post("/api/command",headers=auth(),json=command("open_session",{"table_id":"unknown","guests":3})).status_code==422
    assert client.get("/api/state",headers=auth()).json()["sessions"]==[]

def test_body_limit(client):
    payload={"op":"submit_order","data":{"note":"x"*70000},"key":"1234567890","now":"2026-10-24T12:00:00Z"}
    assert client.post("/api/command",headers=auth(),json=payload).status_code==413
