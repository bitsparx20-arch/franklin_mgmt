"""Rich CRM demo data — visits, POCs, follow-ups, pipeline, bills, notifications."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

DEMO_TAG = "lively_demo"

CITIES = {
    "Delhi": (28.6139, 77.2090),
    "Gurugram": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462),
    "Chandigarh": (30.7333, 76.7794),
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Nagpur": (21.1458, 79.0882),
    "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Bangalore": (12.9716, 77.5946),
    "Kochi": (9.9312, 76.2673),
    "Coimbatore": (11.0168, 76.9558),
    "Kolkata": (22.5726, 88.3639),
    "Bhubaneswar": (20.2961, 85.8245),
    "Guwahati": (26.1445, 91.7362),
    "Ranchi": (23.3441, 85.3096),
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

# Per-regional salesperson demo packs (email must match seeds_team.py)
REGION_PACKS: list[dict[str, Any]] = [
    {
        "email": "swapnil@franklinwardcorpp.com",
        "ping_city": "Bangalore",
        "visits": [
            ("Precision Tools Bangalore", "Fabricator", "Bangalore", "Completed", "Chain block demo — strong interest in lifting gear."),
            ("Reddy Logistics Hub", "Transporter", "Hyderabad", "Completed", "Fleet fasteners audit; WhatsApp follow-up set."),
            ("Chennai Port Warehousing", "PSU", "Chennai", "Follow-up", "Vendor code documentation pending."),
            ("Coimbatore Engineering Works", "Fabricator", "Coimbatore", "Completed", "Plant tour; M16 bolt trial order discussed."),
            ("Kerala Steel Traders", "Dealer", "Kochi", "Follow-up", "Monsoon stock-up — quote for hex nuts by Monday."),
            ("AP Infra Projects", "PSU", "Hyderabad", "Converted", "Tender shortlist — deal opened in pipeline."),
            ("Tirupati Auto Components", "Dealer", "Chennai", "Completed", "Introduced welding rod and cutting disc SKUs."),
        ],
        "pocs": [
            ("Precision Tools Bangalore", "Ananya Iyer", "Technical Buyer", "+919955443322", "Bangalore", "Fabricator"),
            ("Reddy Logistics Hub", "Karthik Reddy", "Operations Head", "+919966554433", "Hyderabad", "Transporter"),
            ("Chennai Port Warehousing", "Ramesh Venkat", "Procurement", "+919944221100", "Chennai", "PSU"),
            ("Kerala Steel Traders", "Thomas Mathew", "Owner", "+919877112233", "Kochi", "Dealer"),
            ("AP Infra Projects", "Srinivas Rao", "Project Manager", "+919888776655", "Hyderabad", "PSU"),
        ],
        "deals": [
            ("Precision Tools Bangalore", "Fabricator", "Bangalore", "NEGOTIATION", 560000, 7),
            ("Reddy Logistics Hub", "Transporter", "Hyderabad", "INTERESTED", 220000, 5),
            ("Chennai Port Warehousing", "PSU", "Chennai", "COLD_LEAD", 720000, 1),
            ("Coimbatore Engineering Works", "Fabricator", "Coimbatore", "CONTACTED", 310000, 3),
            ("Kerala Steel Traders", "Dealer", "Kochi", "INTERESTED", 145000, 4),
            ("AP Infra Projects", "PSU", "Hyderabad", "WON", 485000, 9),
            ("Tirupati Auto Components", "Dealer", "Chennai", "WON", 198000, 6),
        ],
        "bill_clients": [
            "AP Infra Projects", "Tirupati Auto Components", "Precision Tools Bangalore",
            "Reddy Logistics Hub", "Kerala Steel Traders",
        ],
    },
    {
        "email": "chirodeep@franklinwardcorpp.com",
        "ping_city": "Kolkata",
        "visits": [
            ("Kolkata Iron Traders", "Dealer", "Kolkata", "Follow-up", "Price negotiation on hex nuts — competitor undercut."),
            ("Odisha Mining Supplies", "PSU", "Bhubaneswar", "Completed", "Safety PPE inquiry for site crews."),
            ("Eastern Freight Lines", "Transporter", "Kolkata", "Completed", "Met fleet manager; annual fastener contract."),
            ("Guwahati Industrial Depot", "Dealer", "Guwahati", "Completed", "Stock check — grinding wheels reordered."),
            ("Jharkhand Steel Fabricators", "Fabricator", "Ranchi", "Follow-up", "Plate thickness spec confirmation needed."),
            ("NEPCO Construction", "PSU", "Guwahati", "Converted", "Sample anchor bolts approved — PO expected."),
            ("Bhubaneswar Bolt Mart", "Dealer", "Bhubaneswar", "Completed", "Walk-in; added 2 POCs for Q3 supply."),
        ],
        "pocs": [
            ("Kolkata Iron Traders", "Debajyoti Sen", "Purchase Head", "+919811223344", "Kolkata", "Dealer"),
            ("Odisha Mining Supplies", "Pradeep Mohanty", "Stores Incharge", "+919822334455", "Bhubaneswar", "PSU"),
            ("Eastern Freight Lines", "Soma Banerjee", "Fleet Coordinator", "+919833445566", "Kolkata", "Transporter"),
            ("Guwahati Industrial Depot", "Arun Das", "Owner", "+919844556677", "Guwahati", "Dealer"),
            ("Jharkhand Steel Fabricators", "Manoj Singh", "Production Head", "+919855667788", "Ranchi", "Fabricator"),
        ],
        "deals": [
            ("Kolkata Iron Traders", "Dealer", "Kolkata", "LOST", 140000, 6),
            ("Odisha Mining Supplies", "PSU", "Bhubaneswar", "NEGOTIATION", 380000, 5),
            ("Eastern Freight Lines", "Transporter", "Kolkata", "INTERESTED", 165000, 4),
            ("Guwahati Industrial Depot", "Dealer", "Guwahati", "WON", 242000, 8),
            ("Jharkhand Steel Fabricators", "Fabricator", "Ranchi", "CONTACTED", 295000, 2),
            ("NEPCO Construction", "PSU", "Guwahati", "WON", 520000, 10),
            ("Bhubaneswar Bolt Mart", "Dealer", "Bhubaneswar", "COLD_LEAD", 88000, 1),
        ],
        "bill_clients": [
            "Guwahati Industrial Depot", "NEPCO Construction", "Eastern Freight Lines",
            "Odisha Mining Supplies", "Bhubaneswar Bolt Mart",
        ],
    },
    {
        "email": "manish@franklinwardcorpp.com",
        "ping_city": "Delhi",
        "visits": [
            ("Bharat Fabricators Pvt Ltd", "Fabricator", "Delhi", "Completed", "Annual bolt contract discussion; catalogue left."),
            ("Sharma Transports", "Transporter", "Gurugram", "Follow-up", "Fleet expansion — M20 nuts quote by Friday."),
            ("NTPC Bongaigaon Site", "PSU", "Delhi", "Follow-up", "Tender window opens next month."),
            ("Om Steel Fabrication", "Fabricator", "Noida", "Completed", "Plant tour; capacity 200T/month confirmed."),
            ("BlueLine Dealers NCR", "Dealer", "Gurugram", "Converted", "Signed MOU for quarterly supply."),
            ("Hindustan Bolt House", "Dealer", "Delhi", "Completed", "Walk-in reorder for washers and nuts."),
            ("Jaipur Engineering Corp", "Fabricator", "Jaipur", "Follow-up", "Sample plates dispatched — awaiting feedback."),
        ],
        "pocs": [
            ("Bharat Fabricators Pvt Ltd", "Rajesh Sharma", "Plant Manager", "+919876543210", "Delhi", "Fabricator"),
            ("Sharma Transports", "Priya Nair", "Fleet Coordinator", "+919812345678", "Gurugram", "Transporter"),
            ("NTPC Bongaigaon Site", "Col. Vikram Singh", "Procurement", "+919811223344", "Delhi", "PSU"),
            ("Om Steel Fabrication", "Suresh Kumar", "Production Head", "+919944332211", "Noida", "Fabricator"),
            ("BlueLine Dealers NCR", "Rohit Malhotra", "Owner", "+919933221100", "Gurugram", "Dealer"),
        ],
        "deals": [
            ("Bharat Fabricators Pvt Ltd", "Fabricator", "Delhi", "NEGOTIATION", 420000, 8),
            ("Sharma Transports", "Transporter", "Gurugram", "INTERESTED", 185000, 4),
            ("NTPC Bongaigaon Site", "PSU", "Delhi", "CONTACTED", 890000, 2),
            ("Om Steel Fabrication", "Fabricator", "Noida", "WON", 445000, 11),
            ("BlueLine Dealers NCR", "Dealer", "Gurugram", "WON", 198000, 6),
            ("Hindustan Bolt House", "Dealer", "Delhi", "INTERESTED", 132000, 3),
            ("Jaipur Engineering Corp", "Fabricator", "Jaipur", "COLD_LEAD", 275000, 1),
        ],
        "bill_clients": [
            "Om Steel Fabrication", "BlueLine Dealers NCR", "Bharat Fabricators Pvt Ltd",
            "Hindustan Bolt House", "Sharma Transports",
        ],
    },
    {
        "email": "thomas.philip@franklinwardcorpp.com",
        "ping_city": "Mumbai",
        "visits": [
            ("Mumbai Steel Dealers", "Dealer", "Mumbai", "Completed", "Stock check done; grinding wheels reordered."),
            ("Patel Engineering Works", "Fabricator", "Mumbai", "Converted", "PO received for plates — deal created."),
            ("Western Carriers LLP", "Transporter", "Mumbai", "Follow-up", "Lost last quote — revisit with 8% discount."),
            ("Ahmedabad Fasteners Mart", "Dealer", "Ahmedabad", "Completed", "Walk-in; added 3 POCs."),
            ("Pune Auto Forge", "Fabricator", "Pune", "Completed", "Introduced new welding rod SKU."),
            ("Metro Rail Supplies", "PSU", "Mumbai", "Follow-up", "Documentation for vendor empanelment."),
            ("Nagpur Industrial Hub", "Dealer", "Nagpur", "Completed", "Central India distribution tie-up discussed."),
        ],
        "pocs": [
            ("Mumbai Steel Dealers", "Amit Desai", "Purchase Head", "+919900112233", "Mumbai", "Dealer"),
            ("Patel Engineering Works", "Jay Patel", "Director", "+919877665544", "Mumbai", "Fabricator"),
            ("Western Carriers LLP", "Farhan Sheikh", "Operations", "+919866778899", "Mumbai", "Transporter"),
            ("Ahmedabad Fasteners Mart", "Ketan Shah", "Owner", "+919855990011", "Ahmedabad", "Dealer"),
            ("Pune Auto Forge", "Neha Gupta", "Store Incharge", "+919988776655", "Pune", "Fabricator"),
        ],
        "deals": [
            ("Mumbai Steel Dealers", "Dealer", "Mumbai", "WON", 310000, 12),
            ("Patel Engineering Works", "Fabricator", "Mumbai", "WON", 275000, 9),
            ("Western Carriers LLP", "Transporter", "Mumbai", "LOST", 98000, 4),
            ("Ahmedabad Fasteners Mart", "Dealer", "Ahmedabad", "CONTACTED", 175000, 3),
            ("Pune Auto Forge", "Fabricator", "Pune", "NEGOTIATION", 340000, 6),
            ("Metro Rail Supplies", "PSU", "Mumbai", "NEGOTIATION", 650000, 5),
            ("Nagpur Industrial Hub", "Dealer", "Nagpur", "INTERESTED", 118000, 2),
        ],
        "bill_clients": [
            "Mumbai Steel Dealers", "Patel Engineering Works", "Ahmedabad Fasteners Mart",
            "Pune Auto Forge", "Nagpur Industrial Hub",
        ],
    },
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
    One regional pack per salesperson (Swapnil, ChiroDeep, Manish, Thomas Philip).
    """
    manager = await db.users.find_one({"email": "manager@franklinwardcorpp.com"})
    admin = await db.users.find_one({"email": "admin@franklinwardcorpp.com"})
    ceo = await db.users.find_one({"email": "ceo@franklinwardcorpp.com"})

    packs: list[tuple[dict, dict]] = []
    for pack in REGION_PACKS:
        sp = await db.users.find_one({"email": pack["email"]})
        if sp:
            packs.append((pack, sp))

    if not packs:
        sp = await db.users.find_one({"role": "salesperson"})
        if not sp:
            return {"ok": False, "error": "No users in DB. Run seed_team.py or restart API on empty DB."}
        packs = [(REGION_PACKS[0], sp)]

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
    pocs: list[dict] = []
    followups: list[dict] = []
    deals: list[dict] = []
    bills: list[dict] = []
    due_offsets = [-3, -1, 0, 0, 1, 2, 5, 7, -2, 0]
    global_idx = 0

    for pack, sp in packs:
        visit_by_client: dict[str, str] = {}
        pack_pocs: list[dict] = []

        for vi, (cname, ctype, city, status, remarks) in enumerate(pack["visits"]):
            lat, lng = _coords(city, global_idx)
            vid = str(uuid.uuid4())
            vdate = now - timedelta(days=(global_idx % 40) + 1, hours=global_idx % 8)
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
            global_idx += 1

        for pi, (cname, pname, desig, mobile, area, ctype) in enumerate(pack["pocs"]):
            pid = str(uuid.uuid4())
            poc = {
                "id": pid,
                "visit_id": visit_by_client.get(cname),
                "client_name": cname,
                "client_type": ctype,
                "poc_name": pname,
                "designation": desig,
                "mobile": mobile,
                "email": f"{pname.split()[0].lower()}@demo-client.in",
                "whatsapp": mobile,
                "best_time": "10am–1pm" if pi % 2 == 0 else "2pm–5pm",
                "preferred_method": ["Call", "WhatsApp", "Email", "Visit"][pi % 4],
                "notes": f"Key contact for {cname}",
                "area": area,
                "salesperson_id": sp["id"],
                "salesperson_name": sp["name"],
                "created_at": _iso(now - timedelta(days=pi + 2)),
                DEMO_TAG: True,
            }
            pocs.append(poc)
            pack_pocs.append(poc)

        for fi, poc in enumerate(pack_pocs):
            due = (now + timedelta(days=due_offsets[fi % len(due_offsets)])).date().isoformat()
            status = "completed" if fi in (1, 3) else "pending"
            logs = []
            if status == "completed":
                logs = [{
                    "action": ["Called", "WhatsApp Sent", "Visited"][fi % 3],
                    "notes": "Demo completed follow-up",
                    "at": _iso(now - timedelta(days=1)),
                    "by": sp["name"],
                }]
            followups.append({
                "id": str(uuid.uuid4()),
                "poc_id": poc["id"],
                "poc_name": poc["poc_name"],
                "client_name": poc["client_name"],
                "salesperson_id": sp["id"],
                "salesperson_name": sp["name"],
                "due_date": due,
                "notes": f"Follow up on {poc['client_name']} — pricing / sample dispatch",
                "status": status,
                "logs": logs,
                "escalated": fi == 0 and status == "pending",
                "created_at": _iso(now - timedelta(days=5 + fi)),
                DEMO_TAG: True,
            })

        for di, (cname, ctype, area, stage, value, touch) in enumerate(pack["deals"]):
            poc = pack_pocs[di % len(pack_pocs)]
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
                "last_contacted": _iso(now - timedelta(days=(global_idx + di) % 14)),
                "next_follow_up": _iso(now + timedelta(days=((global_idx + di) % 5) - 2)),
                "created_at": _iso(now - timedelta(days=20 + di)),
                "notes": f"Demo pipeline — {stage.replace('_', ' ').title()}",
                "lost_reason": "Price mismatch" if stage == "LOST" else None,
                DEMO_TAG: True,
            })

        for bi, client in enumerate(pack["bill_clients"]):
            month_offset = bi + (hash(sp["email"]) % 3)
            p1 = products[month_offset % len(products)]
            p2 = products[(month_offset + 2) % len(products)]
            qty1, qty2 = 40 + month_offset * 12, 4 + month_offset
            line1_amt = qty1 * p1["unit_price"]
            line2_amt = qty2 * p2["unit_price"]
            subtotal = line1_amt + line2_amt
            gst = subtotal * 0.18
            discount_pct = 5 if month_offset % 3 == 0 else 0
            discount_amt = subtotal * (discount_pct / 100)
            grand = subtotal - discount_amt + gst
            bill_date = now.replace(day=min(15 + bi, 28)) - timedelta(days=30 * (bi + 1))
            bills.append({
                "id": str(uuid.uuid4()),
                "invoice_no": f"FW-{sp['name'][:3].upper()}-{2025}{bi + 1:02d}-{month_offset:02d}",
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
                "notes": f"Demo invoice — {sp['name']} ({pack.get('ping_city', 'region')})",
                "created_at": _iso(bill_date),
                DEMO_TAG: True,
            })

        ping_city = pack.get("ping_city", "Delhi")
        lat, lng = _coords(ping_city, global_idx + 5)
        await db.users.update_one(
            {"id": sp["id"]},
            {"$set": {
                "last_ping_lat": lat,
                "last_ping_lng": lng,
                "last_ping_at": _iso(now - timedelta(minutes=10 + len(packs) * 3)),
            }},
        )

    salespeople = [sp for _, sp in packs]
    notifications: list[dict] = []
    notify_users = [u for u in (ceo, manager, admin, *salespeople[:2]) if u]
    titles = [
        ("Deal Won", "AP Infra Projects closed WON — Swapnil to raise invoice.", "success"),
        ("Overdue Follow-up", "ChiroDeep has an escalated follow-up at Kolkata Iron Traders.", "warning"),
        ("New visit logged", "Thomas Philip completed visit at Mumbai Steel Dealers.", "info"),
        ("Pipeline alert", "₹12.4L in NEGOTIATION across all regions.", "info"),
        ("Bill pending approval", "Discount invoice needs admin approval.", "warning"),
        ("Weekly target", "National team at 72% of monthly target — 6 days left.", "info"),
        ("Live GPS ping", "Manish broadcast location from Delhi NCR.", "info"),
        ("Regional win", "NEPCO Construction (East) — ₹5.2L billed.", "success"),
    ]
    for i, (title, body, kind) in enumerate(titles):
        u = notify_users[i % len(notify_users)]
        notifications.append({
            "id": str(uuid.uuid4()),
            "user_id": u["id"],
            "title": title,
            "body": body,
            "kind": kind,
            "read": i > 3,
            "created_at": _iso(now - timedelta(hours=i * 5)),
            DEMO_TAG: True,
        })

    sms_logs = []
    for i, sp in enumerate(salespeople[:2]):
        sms_logs.append({
            "id": str(uuid.uuid4()),
            "to": sp.get("phone", "+919000000001"),
            "message": f"Reminder: Follow up with your top pipeline deal today — {sp['name']}.",
            "channel": "sms",
            "status": "sent",
            "detail": {"status": "sent", "demo": True},
            "sent_at": _iso(now - timedelta(days=1, hours=i)),
            DEMO_TAG: True,
        })
    if pocs:
        sms_logs.append({
            "id": str(uuid.uuid4()),
            "to": pocs[0]["whatsapp"],
            "message": "Thank you for meeting Franklin Wardcorpp. Quote attached.",
            "channel": "whatsapp",
            "status": "queued",
            "detail": {"status": "queued", "demo": True},
            "sent_at": _iso(now - timedelta(hours=4)),
            DEMO_TAG: True,
        })

    await db.visits.insert_many(visits)
    await db.pocs.insert_many(pocs)
    await db.followups.insert_many(followups)
    await db.deals.insert_many(deals)
    await db.bills.insert_many(bills)
    await db.notifications.insert_many(notifications)
    if sms_logs:
        await db.sms_logs.insert_many(sms_logs)

    per_rep = {}
    for pack, sp in packs:
        sid = sp["id"]
        per_rep[sp["name"]] = {
            "visits": sum(1 for v in visits if v["salesperson_id"] == sid),
            "pocs": sum(1 for p in pocs if p["salesperson_id"] == sid),
            "deals": sum(1 for d in deals if d["salesperson_id"] == sid),
            "bills": sum(1 for b in bills if b["salesperson_id"] == sid),
            "followups": sum(1 for f in followups if f["salesperson_id"] == sid),
        }

    return {
        "ok": True,
        "replaced": replace,
        "salespeople_seeded": [sp["name"] for _, sp in packs],
        "per_rep": per_rep,
        "counts": {
            "visits": len(visits),
            "pocs": len(pocs),
            "followups": len(followups),
            "deals": len(deals),
            "bills": len(bills),
            "notifications": len(notifications),
            "sms_logs": len(sms_logs),
        },
        "hint": "Login as swapnil@ / chirodeep@ / manish@ / thomas.philip@ (sales123) or CEO for full view.",
    }
