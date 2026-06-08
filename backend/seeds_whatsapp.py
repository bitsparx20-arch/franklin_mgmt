"""Sample POCs + follow-ups for SpringEdge WhatsApp testing."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

DEMO_TAG = "whatsapp_demo"


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def seed_whatsapp_samples(db) -> dict[str, Any]:
    """
    Inserts POCs with mobile/WhatsApp numbers and pending follow-ups due today.
    Uses SPRINGEDGE_TEST_PHONE for the primary POC (your real number for live tests).
    """
    test_phone = (os.environ.get("SPRINGEDGE_TEST_PHONE") or "").strip()

    sp = await db.users.find_one({"email": "swapnil@franklinwardcorpp.com"})
    if not sp:
        sp = await db.users.find_one({"role": "salesperson"})
    if not sp:
        return {"ok": False, "error": "No salesperson user found. Start the API once to seed users."}

    await db.pocs.delete_many({DEMO_TAG: True})
    await db.followups.delete_many({DEMO_TAG: True})

    today = _now().date().isoformat()
    primary_phone = test_phone or sp.get("phone") or "+919000000099"

    samples = [
        {
            "client_name": "WhatsApp Test Co.",
            "poc_name": "You (test recipient)",
            "mobile": primary_phone,
            "whatsapp": primary_phone,
            "designation": "Procurement Head",
            "area": "Delhi NCR",
            "notes": "Primary SpringEdge WhatsApp test — set SPRINGEDGE_TEST_PHONE in .env",
        },
        {
            "client_name": "Bharat Fabricators",
            "poc_name": "Mr. Rajesh Sharma",
            "mobile": "+919876543210",
            "whatsapp": "+919876543210",
            "designation": "Plant Manager",
            "area": "Delhi",
            "notes": "Demo POC #2",
        },
        {
            "client_name": "Sharma Transports",
            "poc_name": "Ms. Priya Nair",
            "mobile": "+919812345678",
            "whatsapp": "+919812345678",
            "designation": "Fleet Coordinator",
            "area": "Gurugram",
            "notes": "Demo POC #3",
        },
    ]

    pocs = []
    followups = []
    for i, s in enumerate(samples):
        poc_id = str(uuid.uuid4())
        poc = {
            "id": poc_id,
            "visit_id": None,
            "client_name": s["client_name"],
            "client_type": "Fabricator" if i == 0 else ("Transporter" if i == 2 else "Dealer"),
            "poc_name": s["poc_name"],
            "designation": s["designation"],
            "mobile": s["mobile"],
            "email": f"demo{i + 1}@example.com",
            "whatsapp": s["whatsapp"],
            "best_time": "10am–12pm",
            "preferred_method": "WhatsApp",
            "notes": s["notes"],
            "area": s["area"],
            "salesperson_id": sp["id"],
            "salesperson_name": sp["name"],
            "created_at": _iso(_now()),
            DEMO_TAG: True,
        }
        pocs.append(poc)
        followups.append({
            "id": str(uuid.uuid4()),
            "poc_id": poc_id,
            "poc_name": s["poc_name"],
            "client_name": s["client_name"],
            "salesperson_id": sp["id"],
            "salesperson_name": sp["name"],
            "due_date": today,
            "notes": f"SpringEdge WhatsApp demo — log action 'WhatsApp Sent' to trigger send to {s['whatsapp']}",
            "status": "pending",
            "logs": [],
            "escalated": False,
            "created_at": _iso(_now()),
            DEMO_TAG: True,
        })

    await db.pocs.insert_many(pocs)
    await db.followups.insert_many(followups)

    return {
        "ok": True,
        "salesperson": sp["email"],
        "test_phone": primary_phone,
        "pocs": len(pocs),
        "followups": len(followups),
        "hint": "Login as swapnil@franklinwardcorpp.com, open Follow-ups, Log action, choose WhatsApp Sent",
    }
