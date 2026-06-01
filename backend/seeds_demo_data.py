"""Rich CRM demo data — visits, POCs, follow-ups, pipeline, bills, notifications."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

DEMO_TAG = "lively_demo"

# City coordinates (lat, lng) with small jitter per record
CITIES = {
    "Delhi": (28.6139, 77.2090),
    "Gurugram": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Kolkata": (22.5726, 88.3639),
    "Bangalore": (12.9716, 77.5946),
}

EXTRA_PRODUCTS = [
    {"name": "Stainless Washer M12", "sku": "FW-WSH-M12", "unit_price": 12, "category": "Fasteners", "gst_percent": 18},
    {"name": "Anchor Bolt 10x100", "sku": "FW-ANC-10", "unit_price": 68, "category": "Fasteners", "gst_percent": 18},
    {"name": "Steel Plate 10mm", "sku": "FW-PLT-10", "unit_price": 3200, "category": "Plates", "gst_percent": 18},
    {"name": "Cutting Disc 4in", "sku": "FW-CD-4", "unit_price": 42, "category": "Consumables", "gst_percent": 18},
    {"name": "Safety Gloves (pair)", "sku": "FW-SFG-01", "unit_price": 180, "category": "PPE", "gst_percent": 12},
    {"name": "Industrial Lubricant 5L", "sku": "FW-LUB-5", "unit_price": 1450, "category": "Consumables", "gst_percent": 18},
    {"name": "Chain Block 2T", "sku": "FW-CHN-2T", "unit_price": 8900, "category": "Lifting", "gst_percent": 18},
    {"name": "PVC Hose 25mm/m", "sku": "FW-HOS-25", "unit_price": 95, "category": "Hoses", "gst_percent": 18},
]

VISIT_SAMPLES = [
    ("Bharat Fabricators Pvt Ltd", "Fabricator", "Delhi", "Completed", "Discussed annual bolt contract; left catalogue."),
    ("Sharma Transports", "Transporter", "Gurugram", "Follow-up", "Fleet expansion — needs M20 nuts quote by Friday."),
    ("Mumbai Steel Dealers", "Dealer", "Mumbai", "Completed", "Stock check done; reordered grinding wheels."),
    ("NTPC Bongaigaon Site", "PSU", "Delhi", "Follow-up", "Tender window opens next month."),
    ("Patel Engineering Works", "Fabricator", "Mumbai", "Converted", "PO received for plates — deal created."),
    ("Gupta Auto Components", "Dealer", "Pune", "Completed", "Introduced new welding rod SKU."),
    ("Reddy Logistics Hub", "Transporter", "Hyderabad", "Completed", "Met fleet manager; WhatsApp follow-up set."),
    ("Kolkata Iron Traders", "Dealer", "Kolkata", "Follow-up", "Price negotiation on hex nuts."),
    ("Precision Tools Bangalore", "Fabricator", "Bangalore", "Completed", "Demo of chain block; strong interest."),
    ("Ahmedabad Fasteners Mart", "Dealer", "Ahmedabad", "Completed", "Walk-in; added 3 POCs."),
    ("Noida Industrial Park — Site B", "Other", "Noida", "Completed", "Gate pass visit; safety gear inquiry."),
    ("Western Carriers LLP", "Transporter", "Mumbai", "Follow-up", "Lost last quote — revisit with discount."),
    ("Om Steel Fabrication", "Fabricator", "Delhi", "Completed", "Plant tour; capacity 200T/month."),
    ("Chennai Port Warehousing", "PSU", "Chennai", "Follow-up", "Documentation pending for vendor code."),
    ("BlueLine Dealers NCR", "Dealer", "Gurugram", "Converted", "Signed MOU for quarterly supply."),
]

POC_SAMPLES = [
    ("Bharat Fabricators Pvt Ltd", "Rajesh Sharma", "Plant Manager", "+919876543210", "Delhi", "Fabricator"),
    ("Sharma Transports", "Priya Nair", "Fleet Coordinator", "+919812345678", "Gurugram", "Transporter"),
    ("Mumbai Steel Dealers", "Amit Desai", "Purchase Head", "+919900112233", "Mumbai", "Dealer"),
    ("NTPC Bongaigaon Site", "Col. Vikram Singh", "Procurement", "+919811223344", "Delhi", "PSU"),
    ("Patel Engineering Works", "Jay Patel", "Director", "+919877665544", "Mumbai", "Fabricator"),
    ("Gupta Auto Components", "Neha Gupta", "Store Incharge", "+919988776655", "Pune", "Dealer"),
    ("Reddy Logistics Hub", "Karthik Reddy", "Operations", "+919966554433", "Hyderabad", "Transporter"),
    ("Precision Tools Bangalore", "Ananya Iyer", "Technical Buyer", "+919955443322", "Bangalore", "Fabricator"),
    ("Om Steel Fabrication", "Suresh Kumar", "Production Head", "+919944332211", "Delhi", "Fabricator"),
    ("BlueLine Dealers NCR", "Rohit Malhotra", "Owner", "+919933221100", "Gurugram", "Dealer"),
]

DEAL_SAMPLES = [
    ("Bharat Fabricators Pvt Ltd", "Fabricator", "Delhi", "NEGOTIATION", 420000, 8),
    ("Sharma Transports", "Transporter", "Gurugram", "INTERESTED", 185000, 4),
    ("Mumbai Steel Dealers", "Dealer", "Mumbai", "WON", 310000, 12),
    ("NTPC Bongaigaon Site", "PSU", "Delhi", "CONTACTED", 890000, 2),
    ("Patel Engineering Works", "Fabricator", "Mumbai", "WON", 275000, 9),
    ("Gupta Auto Components", "Dealer", "Pune", "COLD_LEAD", 95000, 1),
    ("Reddy Logistics Hub", "Transporter", "Hyderabad", "INTERESTED", 220000, 5),
    ("Kolkata Iron Traders", "Dealer", "Kolkata", "LOST", 140000, 6),
    ("Precision Tools Bangalore", "Fabricator", "Bangalore", "NEGOTIATION", 560000, 7),
    ("Ahmedabad Fasteners Mart", "Dealer", "Ahmedabad", "CONTACTED", 175000, 3),
    ("Western Carriers LLP", "Transporter", "Mumbai", "LOST", 98000, 4),
    ("Om Steel Fabrication", "Fabricator", "Delhi", "WON", 445000, 11),
    ("Chennai Port Warehousing", "PSU", "Chennai", "COLD_LEAD", 720000, 1),
    ("BlueLine Dealers NCR", "Dealer", "Gurugram", "WON", 198000, 6),
    ("Hindustan Bolt House", "Dealer", "Delhi", "INTERESTED", 132000, 3),
    ("Metro Rail Supplies", "PSU", "Mumbai", "NEGOTIATION", 650000, 5),
]

BILL_CLIENTS = [
    "Mumbai Steel Dealers",
    "Patel Engineering Works",
    "Om Steel Fabrication",
    "BlueLine Dealers NCR",
    "Bharat Fabricators Pvt Ltd",
    "Precision Tools Bangalore",
    "Gupta Auto Components",
    "Reddy Logistics Hub",
    "Ahmedabad Fasteners Mart",
    "Sharma Transports",
    "Hindustan Bolt House",
    "Kolkata Iron Traders",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _coords(city: str, n: int) -> tuple[float, float]:
    base = CITIES.get(city, CITIES["Delhi"])
    jitter = (n % 7) * 0.008 - 0.02
    return round(base[0] + jitter, 6), round(base[1] + jitter * 1.3, 6)


async def _ensure_extra_products(db) -> list[dict]:
    existing: set[str] = set()
    async for p in db.products.find({}, {"sku": 1}):
        existing.add(p["sku"])
    to_insert = []
    for p in EXTRA_PRODUCTS:
        if p["sku"] in existing:
            continue
        to_insert.append({**p, "id": str(uuid.uuid4()), "created_at": _iso(_now())})
    if to_insert:
        await db.products.insert_many(to_insert)
    return await db.products.find({}, {"_id": 0}).to_list(100)


async def _clear_demo(db) -> None:
    filt = {DEMO_TAG: True}
    for coll in ("visits", "pocs", "followups", "deals", "bills", "notifications", "sms_logs"):
        await db[coll].delete_many(filt)


async def seed_lively_demo(db, *, replace: bool = True) -> dict[str, Any]:
    """
    Insert rich sample CRM data tagged with lively_demo.
    Requires demo users (sales1, sales2, manager) from startup seed.
    """
    sp1 = await db.users.find_one({"email": "sales1@franklinwardcorpp.com"})
    sp2 = await db.users.find_one({"email": "sales2@franklinwardcorpp.com"})
    manager = await db.users.find_one({"email": "manager@franklinwardcorpp.com"})
    admin = await db.users.find_one({"email": "admin@franklinwardcorpp.com"})
    if not sp1:
        sp1 = await db.users.find_one({"role": "salesperson"})
    if not sp2 and sp1:
        sp2 = await db.users.find_one({"role": "salesperson", "id": {"$ne": sp1["id"]}})
    if not sp1:
        return {"ok": False, "error": "No users in DB. Restart API on empty DB or create salespeople first."}

    salespeople = [sp1]
    if sp2:
        salespeople.append(sp2)

    existing = await db.visits.count_documents({DEMO_TAG: True})
    if existing and not replace:
        return {"ok": True, "skipped": True, "message": "Demo data already present. POST with replace=true to refresh."}

    if replace:
        await _clear_demo(db)

    products = await _ensure_extra_products(db)
    if not products:
        return {"ok": False, "error": "No products found. Seed products first."}

    now = _now()
    visits: list[dict] = []
    visit_by_client: dict[str, str] = {}

    for i, (cname, ctype, city, status, remarks) in enumerate(VISIT_SAMPLES):
        sp = salespeople[i % len(salespeople)]
        lat, lng = _coords(city, i)
        vid = str(uuid.uuid4())
        vdate = now - timedelta(days=i % 45, hours=i % 8)
        visit_by_client[cname] = vid
        visits.append({
            "id": vid,
            "client_name": cname,
            "client_type": ctype,
            "location_text": f"{city}, India",
            "lat": lat,
            "lng": lng,
            "remarks": remarks,
            "status": status,
            "salesperson_id": sp["id"],
            "salesperson_name": sp["name"],
            "visit_date": _iso(vdate),
            "created_at": _iso(vdate),
            DEMO_TAG: True,
        })

    pocs: list[dict] = []
    poc_ids: list[str] = []
    for i, (cname, pname, desig, mobile, area, ctype) in enumerate(POC_SAMPLES):
        sp = salespeople[i % len(salespeople)]
        pid = str(uuid.uuid4())
        poc_ids.append(pid)
        pocs.append({
            "id": pid,
            "visit_id": visit_by_client.get(cname),
            "client_name": cname,
            "client_type": ctype,
            "poc_name": pname,
            "designation": desig,
            "mobile": mobile,
            "email": f"{pname.split()[0].lower()}@demo-client.in",
            "whatsapp": mobile,
            "best_time": "10am–1pm" if i % 2 == 0 else "2pm–5pm",
            "preferred_method": ["Call", "WhatsApp", "Email", "Visit"][i % 4],
            "notes": f"Key contact for {cname}",
            "area": area,
            "salesperson_id": sp["id"],
            "salesperson_name": sp["name"],
            "created_at": _iso(now - timedelta(days=i + 2)),
            DEMO_TAG: True,
        })

    today = now.date().isoformat()
    followups: list[dict] = []
    due_offsets = [-3, -1, 0, 0, 1, 2, 5, 7, -2, 0]  # overdue, today, future
    for i, poc in enumerate(pocs[:10]):
        sp = await db.users.find_one({"id": poc["salesperson_id"]})
        due = (now + timedelta(days=due_offsets[i % len(due_offsets)])).date().isoformat()
        status = "completed" if i in (2, 5, 8) else "pending"
        logs = []
        if status == "completed":
            logs = [{
                "action": ["Called", "WhatsApp Sent", "Visited"][i % 3],
                "notes": "Demo completed follow-up",
                "at": _iso(now - timedelta(days=1)),
                "by": sp["name"] if sp else "Demo",
            }]
        followups.append({
            "id": str(uuid.uuid4()),
            "poc_id": poc["id"],
            "poc_name": poc["poc_name"],
            "client_name": poc["client_name"],
            "salesperson_id": poc["salesperson_id"],
            "salesperson_name": poc["salesperson_name"],
            "due_date": due,
            "notes": f"Follow up on {poc['client_name']} — pricing / sample dispatch",
            "status": status,
            "logs": logs,
            "escalated": i == 0 and status == "pending",
            "created_at": _iso(now - timedelta(days=5 + i)),
            DEMO_TAG: True,
        })

    deals: list[dict] = []
    for i, (cname, ctype, area, stage, value, touch) in enumerate(DEAL_SAMPLES):
        sp = salespeople[i % len(salespeople)]
        poc = pocs[i % len(pocs)]
        deals.append({
            "id": str(uuid.uuid4()),
            "client_name": cname,
            "client_type": ctype,
            "area": area,
            "poc_id": poc["id"],
            "poc_name": poc["poc_name"],
            "poc_contact": poc["mobile"],
            "estimated_value": value,
            "stage": stage,
            "salesperson_id": sp["id"],
            "salesperson_name": sp["name"],
            "touchpoints": touch,
            "last_contacted": _iso(now - timedelta(days=i % 14)),
            "next_follow_up": _iso(now + timedelta(days=(i % 5) - 2)),
            "created_at": _iso(now - timedelta(days=20 + i)),
            "notes": f"Demo pipeline — {stage.replace('_', ' ').title()}",
            "lost_reason": "Price mismatch" if stage == "LOST" else None,
            DEMO_TAG: True,
        })

    bills: list[dict] = []
    for month_offset in range(11, -1, -1):
        if month_offset > len(BILL_CLIENTS) - 1 and month_offset > 5:
            continue
        sp = salespeople[month_offset % len(salespeople)]
        client = BILL_CLIENTS[month_offset % len(BILL_CLIENTS)]
        p1, p2 = products[month_offset % len(products)], products[(month_offset + 2) % len(products)]
        qty1, qty2 = 50 + month_offset * 10, 5 + month_offset
        line1_amt = qty1 * p1["unit_price"]
        line2_amt = qty2 * p2["unit_price"]
        subtotal = line1_amt + line2_amt
        gst = subtotal * 0.18
        discount_pct = 5 if month_offset % 3 == 0 else 0
        discount_amt = subtotal * (discount_pct / 100)
        grand = subtotal - discount_amt + gst
        bill_date = now.replace(day=15) - timedelta(days=30 * month_offset)
        bills.append({
            "id": str(uuid.uuid4()),
            "invoice_no": f"FW-DEMO-{2024}{12 - (month_offset % 12):02d}-{month_offset:02d}",
            "client_name": client,
            "visit_id": None,
            "deal_id": None,
            "salesperson_id": sp["id"],
            "salesperson_name": sp["name"],
            "lines": [
                {
                    "product_id": p1["id"], "product_name": p1["name"], "sku": p1["sku"],
                    "quantity": qty1, "unit_price": p1["unit_price"], "gst_percent": p1.get("gst_percent", 18),
                    "line_amount": round(line1_amt, 2), "line_gst": round(line1_amt * 0.18, 2),
                },
                {
                    "product_id": p2["id"], "product_name": p2["name"], "sku": p2["sku"],
                    "quantity": qty2, "unit_price": p2["unit_price"], "gst_percent": p2.get("gst_percent", 18),
                    "line_amount": round(line2_amt, 2), "line_gst": round(line2_amt * 0.18, 2),
                },
            ],
            "subtotal": round(subtotal, 2),
            "discount_percent": discount_pct,
            "discount_amount": round(discount_amt, 2),
            "gst_total": round(gst, 2),
            "grand_total": round(grand, 2),
            "needs_approval": discount_pct > 0,
            "notes": "Demo invoice for dashboard charts",
            "created_at": _iso(bill_date),
            DEMO_TAG: True,
        })

    notifications: list[dict] = []
    notify_users = [u for u in (manager, admin, sp1, sp2) if u]
    titles = [
        ("Deal Won 🎉", "Mumbai Steel Dealers moved to WON — create invoice.", "success"),
        ("Overdue Follow-up", "Arjun Field missed follow-up with Bharat Fabricators.", "warning"),
        ("New visit logged", "Sneha Field completed visit at Precision Tools Bangalore.", "info"),
        ("Pipeline alert", "₹6.2L in NEGOTIATION stage across North zone.", "info"),
        ("Bill pending approval", "Discount invoice FW-DEMO needs admin approval.", "warning"),
        ("Weekly target", "Team at 68% of monthly target — 8 days left.", "info"),
    ]
    for i, (title, body, kind) in enumerate(titles):
        u = notify_users[i % len(notify_users)]
        notifications.append({
            "id": str(uuid.uuid4()),
            "user_id": u["id"],
            "title": title,
            "body": body,
            "kind": kind,
            "read": i > 2,
            "created_at": _iso(now - timedelta(hours=i * 6)),
            DEMO_TAG: True,
        })

    sms_logs = [
        {
            "id": str(uuid.uuid4()),
            "to": sp1.get("phone", "+919000000001"),
            "message": "Reminder: Follow up with Bharat Fabricators today.",
            "channel": "sms",
            "status": "sent",
            "detail": {"status": "sent", "demo": True},
            "sent_at": _iso(now - timedelta(days=1)),
            DEMO_TAG: True,
        },
        {
            "id": str(uuid.uuid4()),
            "to": pocs[0]["whatsapp"],
            "message": "Thank you for meeting Franklin Wardcorpp. Quote attached.",
            "channel": "whatsapp",
            "status": "queued",
            "detail": {"status": "queued", "demo": True},
            "sent_at": _iso(now - timedelta(hours=4)),
            DEMO_TAG: True,
        },
    ]

    await db.visits.insert_many(visits)
    await db.pocs.insert_many(pocs)
    await db.followups.insert_many(followups)
    await db.deals.insert_many(deals)
    await db.bills.insert_many(bills)
    await db.notifications.insert_many(notifications)
    await db.sms_logs.insert_many(sms_logs)

    # Recent GPS on map for salespeople
    for i, sp in enumerate(salespeople):
        city = sp.get("area", "Delhi NCR").split()[0]
        if city == "Delhi":
            city = "Delhi"
        lat, lng = _coords(city if city in CITIES else "Delhi", i + 3)
        await db.users.update_one(
            {"id": sp["id"]},
            {"$set": {"last_ping_lat": lat, "last_ping_lng": lng, "last_ping_at": _iso(now - timedelta(minutes=15 + i * 5))}},
        )

    return {
        "ok": True,
        "replaced": replace,
        "counts": {
            "visits": len(visits),
            "pocs": len(pocs),
            "followups": len(followups),
            "deals": len(deals),
            "bills": len(bills),
            "notifications": len(notifications),
            "sms_logs": len(sms_logs),
            "extra_products_added": len(EXTRA_PRODUCTS),
        },
        "hint": "Login as ceo@franklinwardcorpp.com and refresh Dashboard, Pipeline, Visits, Bills.",
    }
