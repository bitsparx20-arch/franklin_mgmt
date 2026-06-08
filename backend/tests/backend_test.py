"""
Franklin Wardcorpp CRM - Backend regression test suite.
Covers: auth, users/role-hierarchy, visits, pocs, followups (+escalation),
deals/kanban, products, bills (GST), dashboard/analytics, notifications, reports.
"""
import os
import uuid
import pytest
import requests
from datetime import datetime, timedelta, timezone

BASE = os.environ.get("REACT_APP_BACKEND_URL") or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0].strip()
BASE = BASE.rstrip("/")
API = f"{BASE}/api"

CREDS = {
    "ceo":     ("ceo@franklinwardcorpp.com",     "ceo12345"),
    "admin":   ("admin@franklinwardcorpp.com",   "admin123"),
    "manager": ("manager@franklinwardcorpp.com", "manager123"),
    "sales1":  ("swapnil@franklinwardcorpp.com",  "sales123"),
    "sales2":  ("chirodeep@franklinwardcorpp.com",  "sales123"),
}

# ----------- helpers -------------

def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"Login failed {email}: {r.status_code} {r.text}"
    data = r.json()
    assert "token" in data and "user" in data
    return data["token"], data["user"]

def _h(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

@pytest.fixture(scope="session")
def tokens():
    out = {}
    for k, (e, p) in CREDS.items():
        tok, user = _login(e, p)
        out[k] = {"token": tok, "user": user}
    return out

# ----------- AUTH -------------

class TestAuth:
    def test_login_all_roles(self, tokens):
        for k, v in tokens.items():
            assert v["user"]["email"] == CREDS[k][0]
            assert "password_hash" not in v["user"]
            assert "_id" not in v["user"]

    def test_login_invalid(self):
        r = requests.post(f"{API}/auth/login", json={"email": "ceo@franklinwardcorpp.com", "password": "wrong"})
        assert r.status_code == 401

    def test_me(self, tokens):
        r = requests.get(f"{API}/auth/me", headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200
        assert r.json()["role"] == "ceo"

    def test_me_no_token(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_login_sets_cookie(self):
        r = requests.post(f"{API}/auth/login", json={"email": CREDS["ceo"][0], "password": CREDS["ceo"][1]})
        assert r.status_code == 200
        assert "access_token" in r.cookies

# ----------- USERS / hierarchy -------------

class TestUsers:
    created_ids = []

    def test_ceo_creates_admin(self, tokens):
        email = f"TEST_admin_{uuid.uuid4().hex[:6]}@fr.com"
        r = requests.post(f"{API}/users", headers=_h(tokens["ceo"]["token"]),
                          json={"email": email, "password": "pw12345", "name": "T Admin", "role": "admin"})
        assert r.status_code == 200, r.text
        u = r.json()
        assert u["role"] == "admin" and u["email"] == email.lower()
        TestUsers.created_ids.append(u["id"])
        # verify GET
        g = requests.get(f"{API}/users/{u['id']}", headers=_h(tokens["ceo"]["token"]))
        assert g.status_code == 200 and g.json()["email"] == email.lower()

    def test_admin_creates_manager_and_salesperson(self, tokens):
        for role in ["sales_manager", "salesperson"]:
            email = f"TEST_{role}_{uuid.uuid4().hex[:6]}@fr.com"
            r = requests.post(f"{API}/users", headers=_h(tokens["admin"]["token"]),
                              json={"email": email, "password": "pw12345", "name": f"T {role}", "role": role})
            assert r.status_code == 200, r.text
            TestUsers.created_ids.append(r.json()["id"])

    def test_salesperson_cannot_create_user(self, tokens):
        r = requests.post(f"{API}/users", headers=_h(tokens["sales1"]["token"]),
                          json={"email": "x@x.com", "password": "pw", "name": "x", "role": "salesperson"})
        assert r.status_code == 403

    def test_manager_cannot_create_admin(self, tokens):
        r = requests.post(f"{API}/users", headers=_h(tokens["manager"]["token"]),
                          json={"email": f"TEST_x_{uuid.uuid4().hex[:5]}@x.com", "password": "pw12345",
                                "name": "x", "role": "admin"})
        assert r.status_code == 403

    def test_list_users_scope_salesperson(self, tokens):
        r = requests.get(f"{API}/users", headers=_h(tokens["sales1"]["token"]))
        assert r.status_code == 200
        ids = [u["id"] for u in r.json()]
        assert ids == [tokens["sales1"]["user"]["id"]], f"Salesperson should see only self, got {ids}"

    def test_list_users_scope_manager(self, tokens):
        r = requests.get(f"{API}/users", headers=_h(tokens["manager"]["token"]))
        assert r.status_code == 200
        users = r.json()
        roles = {u["role"] for u in users}
        # Should include self + reports
        assert tokens["manager"]["user"]["id"] in [u["id"] for u in users]
        # Should not include CEO/admin
        assert "ceo" not in roles and "admin" not in roles

    def test_list_users_ceo_sees_all(self, tokens):
        r = requests.get(f"{API}/users", headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200
        roles = {u["role"] for u in r.json()}
        assert {"ceo", "admin", "sales_manager", "salesperson"}.issubset(roles)

    def test_delete_non_admin_role_forbidden(self, tokens):
        r = requests.delete(f"{API}/users/some-id", headers=_h(tokens["sales1"]["token"]))
        assert r.status_code == 403
        r = requests.delete(f"{API}/users/some-id", headers=_h(tokens["manager"]["token"]))
        assert r.status_code == 403

    def test_cleanup_created(self, tokens):
        for uid in TestUsers.created_ids:
            r = requests.delete(f"{API}/users/{uid}", headers=_h(tokens["ceo"]["token"]))
            assert r.status_code == 200

# ----------- VISITS -------------

class TestVisits:
    visit_id = None

    def test_create_visit_autocaptures_sp(self, tokens):
        payload = {"client_name": "TEST_Bharat Fab", "client_type": "Fabricator",
                   "location_text": "Delhi", "lat": 28.6, "lng": 77.2,
                   "remarks": "init", "status": "Completed"}
        r = requests.post(f"{API}/visits", headers=_h(tokens["sales1"]["token"]), json=payload)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["salesperson_id"] == tokens["sales1"]["user"]["id"]
        assert d["salesperson_name"] == tokens["sales1"]["user"]["name"]
        assert d["lat"] == 28.6 and d["lng"] == 77.2
        TestVisits.visit_id = d["id"]

    def test_list_visits_scope_salesperson(self, tokens):
        # sales2 must not see sales1's visit
        r = requests.get(f"{API}/visits", headers=_h(tokens["sales2"]["token"]))
        assert r.status_code == 200
        ids = [v["id"] for v in r.json()]
        assert TestVisits.visit_id not in ids

    def test_list_visits_ceo_sees(self, tokens):
        r = requests.get(f"{API}/visits", headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200
        ids = [v["id"] for v in r.json()]
        assert TestVisits.visit_id in ids

# ----------- POCS + FOLLOWUPS -------------

class TestPocFollowups:
    poc_id = None
    fu_id = None

    def test_create_poc(self, tokens):
        r = requests.post(f"{API}/pocs", headers=_h(tokens["sales1"]["token"]),
                          json={"client_name": "TEST_Client A", "poc_name": "Mr A", "mobile": "+919000000099",
                                "preferred_method": "Call", "area": "Delhi"})
        assert r.status_code == 200, r.text
        TestPocFollowups.poc_id = r.json()["id"]

    def test_list_pocs(self, tokens):
        r = requests.get(f"{API}/pocs", headers=_h(tokens["sales1"]["token"]))
        assert r.status_code == 200
        assert any(p["id"] == TestPocFollowups.poc_id for p in r.json())

    def test_create_followup_overdue(self, tokens):
        due = (datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat()
        r = requests.post(f"{API}/followups", headers=_h(tokens["sales1"]["token"]),
                          json={"poc_id": TestPocFollowups.poc_id, "due_date": due, "notes": "TEST"})
        assert r.status_code == 200, r.text
        TestPocFollowups.fu_id = r.json()["id"]

    def test_list_followups_has_overdue_flag(self, tokens):
        r = requests.get(f"{API}/followups", headers=_h(tokens["sales1"]["token"]))
        assert r.status_code == 200
        match = [f for f in r.json() if f["id"] == TestPocFollowups.fu_id]
        assert match and match[0]["is_overdue"] is True

    def test_log_followup(self, tokens):
        r = requests.post(f"{API}/followups/{TestPocFollowups.fu_id}/log",
                          headers=_h(tokens["sales1"]["token"]),
                          json={"action": "Called", "notes": "spoke briefly"})
        assert r.status_code == 200
        # verify status updated to completed
        r2 = requests.get(f"{API}/followups", headers=_h(tokens["sales1"]["token"]))
        match = [f for f in r2.json() if f["id"] == TestPocFollowups.fu_id]
        assert match[0]["status"] == "completed"
        assert len(match[0]["logs"]) >= 1

    def test_escalate_overdue_forbidden_for_salesperson(self, tokens):
        r = requests.post(f"{API}/followups/escalate-overdue", headers=_h(tokens["sales1"]["token"]))
        assert r.status_code == 403

    def test_escalate_overdue_manager(self, tokens):
        # Create new overdue fu for sales1 -> manager should be notified
        due = (datetime.now(timezone.utc) - timedelta(days=3)).date().isoformat()
        cr = requests.post(f"{API}/followups", headers=_h(tokens["sales1"]["token"]),
                           json={"poc_id": TestPocFollowups.poc_id, "due_date": due, "notes": "TEST esc"})
        assert cr.status_code == 200
        r = requests.post(f"{API}/followups/escalate-overdue", headers=_h(tokens["manager"]["token"]))
        assert r.status_code == 200, r.text
        body = r.json()
        assert "escalated" in body and isinstance(body["escalated"], int)
        # Manager should have at least one notification now
        n = requests.get(f"{API}/notifications", headers=_h(tokens["manager"]["token"]))
        assert n.status_code == 200
        assert any("Escalation" in (x.get("title", "") + x.get("body", "")) or "Overdue" in x.get("title", "")
                   for x in n.json())

# ----------- DEALS -------------

class TestDeals:
    deal_id = None

    def test_create_deal(self, tokens):
        r = requests.post(f"{API}/deals", headers=_h(tokens["sales1"]["token"]),
                          json={"client_name": "TEST_DealCo", "client_type": "Fabricator",
                                "area": "Delhi", "estimated_value": 200000, "stage": "COLD_LEAD"})
        assert r.status_code == 200
        d = r.json()
        TestDeals.deal_id = d["id"]
        assert d["touchpoints"] == 0

    def test_filter_by_stage_area(self, tokens):
        r = requests.get(f"{API}/deals?stage=COLD_LEAD&area=Delhi", headers=_h(tokens["sales1"]["token"]))
        assert r.status_code == 200
        for d in r.json():
            assert d["stage"] == "COLD_LEAD" and d["area"] == "Delhi"

    def test_patch_deal_increments_touchpoints_and_won_notif(self, tokens):
        r = requests.patch(f"{API}/deals/{TestDeals.deal_id}", headers=_h(tokens["sales1"]["token"]),
                           json={"stage": "WON"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["stage"] == "WON" and d["touchpoints"] == 1
        # WON notification for sales1
        n = requests.get(f"{API}/notifications", headers=_h(tokens["sales1"]["token"]))
        assert any("Won" in x.get("title", "") for x in n.json())

    def test_scope_salesperson_cannot_see_others(self, tokens):
        r = requests.get(f"{API}/deals", headers=_h(tokens["sales2"]["token"]))
        ids = [d["id"] for d in r.json()]
        assert TestDeals.deal_id not in ids

# ----------- PRODUCTS -------------

class TestProducts:
    pid = None

    def test_salesperson_create_product_forbidden(self, tokens):
        r = requests.post(f"{API}/products", headers=_h(tokens["sales1"]["token"]),
                          json={"name": "x", "sku": "TEST_X", "unit_price": 100, "category": "x", "gst_percent": 18})
        assert r.status_code == 403

    def test_admin_create_product(self, tokens):
        sku = f"TEST_SKU_{uuid.uuid4().hex[:5]}"
        r = requests.post(f"{API}/products", headers=_h(tokens["admin"]["token"]),
                          json={"name": "TEST Plate", "sku": sku, "unit_price": 1000, "category": "Plates", "gst_percent": 18})
        assert r.status_code == 200
        TestProducts.pid = r.json()["id"]
        TestProducts.sku = sku

    def test_list_products(self, tokens):
        r = requests.get(f"{API}/products", headers=_h(tokens["sales1"]["token"]))
        assert r.status_code == 200
        assert len(r.json()) >= 5

    def test_patch_product(self, tokens):
        r = requests.patch(f"{API}/products/{TestProducts.pid}", headers=_h(tokens["admin"]["token"]),
                           json={"unit_price": 1500})
        assert r.status_code == 200 and r.json()["unit_price"] == 1500

    def test_delete_product(self, tokens):
        r = requests.delete(f"{API}/products/{TestProducts.pid}", headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200

# ----------- BILLS -------------

class TestBills:
    def test_create_bill_no_discount(self, tokens):
        prods = requests.get(f"{API}/products", headers=_h(tokens["sales1"]["token"])).json()
        p = prods[0]
        lines = [{"product_id": p["id"], "product_name": p["name"], "sku": p["sku"],
                  "quantity": 10, "unit_price": p["unit_price"], "gst_percent": p["gst_percent"]}]
        r = requests.post(f"{API}/bills", headers=_h(tokens["sales1"]["token"]),
                          json={"client_name": "TEST_BillClient", "lines": lines, "discount_percent": 0})
        assert r.status_code == 200, r.text
        b = r.json()
        sub = round(10 * p["unit_price"], 2)
        gst = round(sub * p["gst_percent"] / 100, 2)
        assert b["subtotal"] == sub
        assert b["gst_total"] == gst
        assert b["grand_total"] == round(sub + gst, 2)
        assert b["needs_approval"] is False

    def test_create_bill_with_discount_needs_approval(self, tokens):
        prods = requests.get(f"{API}/products", headers=_h(tokens["sales1"]["token"])).json()
        p = prods[0]
        lines = [{"product_id": p["id"], "product_name": p["name"], "sku": p["sku"],
                  "quantity": 2, "unit_price": 1000, "gst_percent": 18}]
        r = requests.post(f"{API}/bills", headers=_h(tokens["sales1"]["token"]),
                          json={"client_name": "TEST_BillDisc", "lines": lines, "discount_percent": 10})
        assert r.status_code == 200
        b = r.json()
        # subtotal=2000, disc=200, gst=360, grand=2160
        assert b["subtotal"] == 2000.0
        assert b["discount_amount"] == 200.0
        assert b["gst_total"] == 360.0
        assert b["grand_total"] == 2160.0
        assert b["needs_approval"] is True

    def test_list_bills_scope(self, tokens):
        r1 = requests.get(f"{API}/bills", headers=_h(tokens["sales2"]["token"]))
        for b in r1.json():
            assert b["salesperson_id"] == tokens["sales2"]["user"]["id"]

# ----------- DASHBOARD -------------

class TestDashboard:
    def test_overview(self, tokens):
        r = requests.get(f"{API}/dashboard/overview", headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200
        d = r.json()
        assert "totals" in d and "stages_summary" in d and "monthly_revenue" in d
        for k in ["visits", "pocs", "deals", "won", "lost", "bills", "revenue", "pipeline_value"]:
            assert k in d["totals"]
        assert len(d["monthly_revenue"]) == 12

    def test_performance(self, tokens):
        r = requests.get(f"{API}/dashboard/performance", headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list) and len(arr) >= 2
        for sp in arr:
            assert "conversion_rate" in sp and "pipeline_conversion" in sp

    def test_funnel(self, tokens):
        r = requests.get(f"{API}/dashboard/funnel", headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200
        assert [s["label"] for s in r.json()["stages"]] == ["Visits", "POCs", "Pipeline", "Won"]

    def test_agent_locations_forbidden_sp(self, tokens):
        r = requests.get(f"{API}/dashboard/agent-locations", headers=_h(tokens["sales1"]["token"]))
        assert r.status_code == 403

    def test_agent_locations_manager(self, tokens):
        r = requests.get(f"{API}/dashboard/agent-locations", headers=_h(tokens["manager"]["token"]))
        assert r.status_code == 200
        # at least sales1's earlier visit (had lat/lng)
        assert isinstance(r.json(), list)

    def test_top_products(self, tokens):
        r = requests.get(f"{API}/dashboard/top-products", headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200 and isinstance(r.json(), list)

# ----------- NOTIFICATIONS -------------

class TestNotifications:
    def test_list_notifications(self, tokens):
        r = requests.get(f"{API}/notifications", headers=_h(tokens["sales1"]["token"]))
        assert r.status_code == 200

    def test_mark_all_read(self, tokens):
        r = requests.post(f"{API}/notifications/mark-all-read", headers=_h(tokens["sales1"]["token"]))
        assert r.status_code == 200
        nr = requests.get(f"{API}/notifications", headers=_h(tokens["sales1"]["token"]))
        for n in nr.json():
            assert n["read"] is True

    def test_mark_single_read(self, tokens):
        # Create a notif by patching a deal to WON
        deals = requests.get(f"{API}/deals", headers=_h(tokens["sales1"]["token"])).json()
        if deals:
            requests.patch(f"{API}/deals/{deals[0]['id']}", headers=_h(tokens["sales1"]["token"]),
                           json={"stage": "WON"})
        n = requests.get(f"{API}/notifications", headers=_h(tokens["sales1"]["token"])).json()
        unread = [x for x in n if not x["read"]]
        if unread:
            r = requests.post(f"{API}/notifications/{unread[0]['id']}/read",
                              headers=_h(tokens["sales1"]["token"]))
            assert r.status_code == 200

# ----------- REPORTS -------------

class TestReports:
    @pytest.mark.parametrize("ep", ["visits", "bills", "pipeline", "pocs"])
    def test_reports(self, tokens, ep):
        r = requests.get(f"{API}/reports/{ep}", headers=_h(tokens["ceo"]["token"]))
        assert r.status_code == 200
        assert isinstance(r.json(), list)
