"""
Franklin Wardcorpp CRM - Enhancement Test Suite (Iteration 3).
Covers: AI chatbot, agent-locations all-agents, ping-location, /reports/overview.
"""
import os
import re
import time
import uuid
import requests
import pytest

BASE = (os.environ.get("REACT_APP_BACKEND_URL")
        or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0].strip()).rstrip("/")
API = f"{BASE}/api"
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

CREDS = {
    "ceo":     ("ceo@franklinwardcorpp.com",     "ceo12345"),
    "admin":   ("admin@franklinwardcorpp.com",   "admin123"),
    "manager": ("manager@franklinwardcorpp.com", "manager123"),
    "sales1":  ("sales1@franklinwardcorpp.com",  "sales123"),
    "sales2":  ("sales2@franklinwardcorpp.com",  "sales123"),
}

def _login(email, pw):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"], r.json()["user"]

def _h(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

@pytest.fixture(scope="module")
def tokens():
    out = {}
    for k, (e, p) in CREDS.items():
        t, u = _login(e, p)
        out[k] = {"token": t, "user": u}
    return out


# ----------- AI CHATBOT -------------

class TestAIChatbot:
    session_id = None

    def test_ai_ask_first_message(self, tokens):
        r = requests.post(f"{API}/ai/ask", headers=_h(tokens["ceo"]["token"]),
                          json={"message": "Summarize my pipeline"}, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "reply" in d and "session_id" in d
        assert isinstance(d["reply"], str) and len(d["reply"]) > 50, f"reply too short: {d['reply']!r}"
        assert UUID_RE.match(d["session_id"]), f"session_id not UUID: {d['session_id']}"
        TestAIChatbot.session_id = d["session_id"]

    def test_ai_ask_continues_session(self, tokens):
        assert TestAIChatbot.session_id is not None
        r = requests.post(f"{API}/ai/ask", headers=_h(tokens["ceo"]["token"]),
                          json={"message": "What did you just summarize? Reply in one short sentence.",
                                "session_id": TestAIChatbot.session_id}, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["session_id"] == TestAIChatbot.session_id
        assert isinstance(d["reply"], str) and len(d["reply"]) > 10

    def test_ai_sessions_list(self, tokens):
        r = requests.get(f"{API}/ai/sessions", headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list) and len(arr) >= 1
        ids = [s.get("session_id") or s.get("id") for s in arr]
        assert TestAIChatbot.session_id in ids, f"created session not in list: {ids}"

    def test_ai_session_messages(self, tokens):
        r = requests.get(f"{API}/ai/sessions/{TestAIChatbot.session_id}/messages",
                         headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200
        msgs = r.json()
        assert isinstance(msgs, list) and len(msgs) >= 4  # 2 user + 2 assistant
        roles = [m.get("role") for m in msgs]
        assert "user" in roles and "assistant" in roles

    def test_ai_ask_salesperson_forbidden(self, tokens):
        r = requests.post(f"{API}/ai/ask", headers=_h(tokens["sales1"]["token"]),
                         json={"message": "hello"})
        assert r.status_code == 403, f"expected 403 got {r.status_code}: {r.text}"


# ----------- AGENT LOCATIONS (enhanced) -------------

class TestAgentLocations:
    def test_returns_all_agents(self, tokens):
        r = requests.get(f"{API}/dashboard/agent-locations", headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list) and len(arr) >= 3, f"expected >=3 (2 sp + 1 mgr), got {len(arr)}"
        # field schema check
        for ent in arr:
            for k in ["salesperson_id", "name", "role", "area", "lat", "lng", "source", "last_seen"]:
                assert k in ent, f"missing {k} in {ent}"
            assert ent["source"] in ("visit", "ping", "default")
        roles = {e["role"] for e in arr}
        assert "salesperson" in roles
        assert "sales_manager" in roles, f"manager missing in roles: {roles}"


# ----------- PING LOCATION -------------

class TestPing:
    def test_ping_then_visible_with_source_ping(self, tokens):
        coords = {"lat": 28.6, "lng": 77.1}
        r = requests.post(f"{API}/users/me/ping-location",
                          headers=_h(tokens["sales1"]["token"]), json=coords)
        assert r.status_code == 200, r.text
        # small delay
        time.sleep(0.3)
        r2 = requests.get(f"{API}/dashboard/agent-locations", headers=_h(tokens["ceo"]["token"]))
        assert r2.status_code == 200
        sp_id = tokens["sales1"]["user"]["id"]
        entry = next((e for e in r2.json() if e["salesperson_id"] == sp_id), None)
        assert entry is not None, "sales1 not in agent-locations"
        assert entry["source"] == "ping", f"expected source=ping got {entry['source']}"
        assert abs(entry["lat"] - 28.6) < 0.001
        assert abs(entry["lng"] - 77.1) < 0.001


# ----------- /reports/overview -------------

class TestReportsOverview:
    def test_overview_structure(self, tokens):
        r = requests.get(f"{API}/reports/overview", headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ["generated_at", "actor", "overview", "performance", "funnel", "top_products", "recent_bills"]:
            assert k in d, f"missing top-level key {k}"
        ov = d["overview"]
        for k in ["totals", "stages_summary", "monthly_revenue"]:
            assert k in ov, f"missing overview.{k}"
        assert isinstance(d["performance"], list)
        assert isinstance(d["funnel"], dict) or isinstance(d["funnel"], list)
        assert isinstance(d["top_products"], list)
        assert isinstance(d["recent_bills"], list)

    def test_overview_salesperson_access(self, tokens):
        # Spec did not explicitly forbid; ensure non-500 (200 or 403 both acceptable)
        r = requests.get(f"{API}/reports/overview", headers=_h(tokens["sales1"]["token"]))
        assert r.status_code in (200, 403)
