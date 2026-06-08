"""Franklin Wardcorpp — core sales team seed (idempotent upsert)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional

# Legacy demo accounts replaced by the real team on upsert.
LEGACY_DEMO_EMAILS = (
    "sales1@franklinwardcorpp.com",
    "sales2@franklinwardcorpp.com",
)

TEAM_MEMBERS: list[dict[str, Any]] = [
    {
        "email": "ceo@franklinwardcorpp.com",
        "name": "Vivek Wadhwa",
        "role": "ceo",
        "designation": "CEO",
        "area": "HQ",
        "phone": "+919820059881",
        "password": "ceo12345",
        "target": 0,
        "reports_to": None,
    },
    {
        "email": "om.wadhwa@franklinwardcorpp.com",
        "name": "OM Wadhwa",
        "role": "ceo",
        "designation": "CEO",
        "area": "HQ",
        "phone": "+919820181658",
        "password": "ceo12345",
        "target": 0,
        "reports_to": None,
    },
    {
        "email": "admin@franklinwardcorpp.com",
        "name": "Ravi Admin",
        "role": "admin",
        "designation": "Operations Admin",
        "area": "HQ",
        "phone": "+91-9000000001",
        "password": "admin123",
        "target": 0,
        "reports_to": "ceo@franklinwardcorpp.com",
    },
    {
        "email": "manager@franklinwardcorpp.com",
        "name": "Joe Jacob",
        "role": "sales_manager",
        "designation": "National Sales Head",
        "area": "National",
        "phone": "+91-9810000003",
        "password": "manager123",
        "target": 8_000_000,
        "reports_to": "ceo@franklinwardcorpp.com",
    },
    {
        "email": "swapnil@franklinwardcorpp.com",
        "name": "Swapnil",
        "role": "salesperson",
        "designation": "Regional Sales Executive — South",
        "area": "Southern Region (TN, Kerala, Karnataka, AP, Telangana)",
        "phone": "+91-9810000004",
        "password": "sales123",
        "target": 2_000_000,
        "reports_to": "manager@franklinwardcorpp.com",
    },
    {
        "email": "chirodeep@franklinwardcorpp.com",
        "name": "ChiroDeep",
        "role": "salesperson",
        "designation": "Regional Sales Executive — East",
        "area": "Eastern Region (WB, Odisha, Jharkhand, Northeast, Nepal)",
        "phone": "+91-9810000005",
        "password": "sales123",
        "target": 2_000_000,
        "reports_to": "manager@franklinwardcorpp.com",
    },
    {
        "email": "manish@franklinwardcorpp.com",
        "name": "Manish",
        "role": "salesperson",
        "designation": "Regional Sales Executive — North",
        "area": "Northern Region (Northern States)",
        "phone": "+91-9810000006",
        "password": "sales123",
        "target": 2_000_000,
        "reports_to": "manager@franklinwardcorpp.com",
    },
    {
        "email": "thomas.philip@franklinwardcorpp.com",
        "name": "Thomas Philip",
        "role": "salesperson",
        "designation": "Regional Sales Executive — West",
        "area": "Western Region (Western States)",
        "phone": "+91-9810000007",
        "password": "sales123",
        "target": 2_000_000,
        "reports_to": "manager@franklinwardcorpp.com",
    },
]


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


async def ensure_team_users(
    db,
    *,
    hash_password: Callable[[str], str],
    remove_legacy: bool = True,
) -> dict[str, Any]:
    """
    Upsert the Franklin sales team by email.
    Updates name, role, designation, area, target, and reporting lines on every run.
    """
    now = _iso(datetime.now(timezone.utc))
    id_by_email: dict[str, str] = {}

    async for u in db.users.find({}, {"id": 1, "email": 1}):
        id_by_email[u["email"]] = u["id"]

    inserted = 0
    updated = 0

    for member in TEAM_MEMBERS:
        email = member["email"].lower()
        payload = {
            "name": member["name"],
            "role": member["role"],
            "designation": member["designation"],
            "area": member["area"],
            "phone": member["phone"],
            "target": member["target"],
            "photo_url": "",
        }
        existing = await db.users.find_one({"email": email})
        if existing:
            await db.users.update_one({"email": email}, {"$set": payload})
            id_by_email[email] = existing["id"]
            updated += 1
        else:
            user_id = str(uuid.uuid4())
            doc = {
                "id": user_id,
                "email": email,
                "password_hash": hash_password(member["password"]),
                **payload,
                "reporting_manager_id": None,
                "created_at": now,
            }
            await db.users.insert_one(doc)
            id_by_email[email] = user_id
            inserted += 1

    for member in TEAM_MEMBERS:
        email = member["email"].lower()
        reports_to = member.get("reports_to")
        manager_id = id_by_email.get(reports_to) if reports_to else None
        await db.users.update_one(
            {"email": email},
            {"$set": {"reporting_manager_id": manager_id}},
        )

    removed = 0
    if remove_legacy:
        result = await db.users.delete_many({"email": {"$in": list(LEGACY_DEMO_EMAILS)}})
        removed = result.deleted_count

    return {
        "ok": True,
        "inserted": inserted,
        "updated": updated,
        "removed_legacy": removed,
        "team_size": len(TEAM_MEMBERS),
        "emails": [m["email"] for m in TEAM_MEMBERS],
    }
