"""Local CRM insights when Bedrock content filters block business queries."""
from __future__ import annotations

from typing import Any, Optional


async def fetch_crm_snapshot(db, actor: dict, *, scoped_filter_async) -> dict[str, Any]:
    q = await scoped_filter_async(actor)
    total_visits = await db.visits.count_documents(q)
    total_pocs = await db.pocs.count_documents(q)
    total_deals = await db.deals.count_documents(q)
    won = await db.deals.count_documents({**q, "stage": "WON"})
    lost = await db.deals.count_documents({**q, "stage": "LOST"})

    stage_summary: dict[str, dict[str, float | int]] = {}
    pipeline_total = 0.0
    async for d in db.deals.find(q, {"_id": 0, "stage": 1, "estimated_value": 1}):
        s = d.get("stage", "?")
        stage_summary.setdefault(s, {"count": 0, "value": 0.0})
        stage_summary[s]["count"] += 1
        val = float(d.get("estimated_value", 0) or 0)
        stage_summary[s]["value"] += val
        if s != "LOST":
            pipeline_total += val

    bills = await db.bills.find(
        q, {"_id": 0, "grand_total": 1, "client_name": 1, "salesperson_name": 1, "lines": 1}
    ).to_list(500)
    revenue = sum(float(b.get("grand_total", 0) or 0) for b in bills)

    sp_q = {"role": "salesperson"}
    if actor["role"] == "sales_manager":
        sp_q["reporting_manager_id"] = actor["id"]
    salespeople = await db.users.find(sp_q, {"_id": 0, "password_hash": 0}).to_list(500)

    perf = []
    for sp in salespeople:
        sp_bills = [b for b in bills if b.get("salesperson_name") == sp["name"]]
        actual = sum(float(b.get("grand_total", 0) or 0) for b in sp_bills)
        target = float(sp.get("target", 0) or 0)
        perf.append({
            "name": sp["name"],
            "area": sp.get("area", ""),
            "target": target,
            "actual": round(actual, 2),
            "conversion": round((actual / target * 100) if target else 0, 1),
        })
    perf.sort(key=lambda x: -x["conversion"])

    prod: dict[str, float] = {}
    for b in bills:
        for ln in b.get("lines", []):
            prod[ln["product_name"]] = prod.get(ln["product_name"], 0) + float(ln.get("line_amount", 0) or 0)
    top_products = sorted(prod.items(), key=lambda x: -x[1])[:5]

    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date().isoformat()
    overdue_q = {**q, "status": "pending", "due_date": {"$lt": today}} if q else {"status": "pending", "due_date": {"$lt": today}}
    overdue = await db.followups.count_documents(overdue_q)

    return {
        "actor": {"name": actor["name"], "role": actor["role"]},
        "totals": {
            "visits": total_visits,
            "pocs": total_pocs,
            "deals": total_deals,
            "won": won,
            "lost": lost,
            "overdue": overdue,
        },
        "pipeline_total": pipeline_total,
        "revenue": revenue,
        "stages": stage_summary,
        "perf": perf,
        "top_products": top_products,
    }


def format_crm_context(snapshot: dict[str, Any]) -> str:
    actor = snapshot["actor"]
    totals = snapshot["totals"]
    scope = (
        "team-wide" if actor["role"] in ("ceo", "admin")
        else "own team" if actor["role"] == "sales_manager"
        else "self"
    )
    lines = [
        "COMPANY: Franklin Wardcorpp (Industrial Fasteners & Steel — India)",
        f"USER: {actor['name']} ({actor['role']})",
        f"SCOPE: {scope}",
        "",
        "== TOTALS ==",
        f"Visits: {totals['visits']} · POCs: {totals['pocs']} · Deals: {totals['deals']} "
        f"(WON: {totals['won']}, LOST: {totals['lost']})",
        f"Pipeline value (excl. lost): ₹{snapshot['pipeline_total']:,.0f}",
        f"Total billed revenue: ₹{snapshot['revenue']:,.0f}",
        f"Overdue follow-ups: {totals['overdue']}",
        "",
        "== KANBAN STAGES ==",
    ]
    for s, info in snapshot["stages"].items():
        lines.append(f"  {s}: {info['count']} deals · ₹{info['value']:,.0f}")
    lines.append("")
    lines.append("== SALESPEOPLE PERFORMANCE (sorted by conversion) ==")
    for p in snapshot["perf"][:10]:
        lines.append(
            f"  {p['name']} ({p['area']}): ₹{p['actual']:,.0f} / target ₹{p['target']:,.0f} · {p['conversion']}%"
        )
    lines.append("")
    lines.append("== TOP PRODUCTS BY REVENUE ==")
    for name, val in snapshot["top_products"]:
        lines.append(f"  {name}: ₹{val:,.0f}")
    return "\n".join(lines)


def _inr(n: float) -> str:
    return f"₹{n:,.0f}"


def local_crm_insight(snapshot: dict[str, Any], message: str) -> Optional[str]:
    """Rule-based answers from live CRM data when the LLM is blocked."""
    q = message.lower()
    totals = snapshot["totals"]
    stages = snapshot["stages"]
    lost_value = float(stages.get("LOST", {}).get("value", 0))
    pipeline = snapshot["pipeline_total"]
    revenue = snapshot["revenue"]
    overdue = totals["overdue"]

    if any(w in q for w in ("leak", "losing", "lost revenue", "leakage", "bleed", "slipping", "gap")):
        early = sum(
            float(stages.get(s, {}).get("value", 0))
            for s in ("COLD_LEAD", "CONTACTED", "INTERESTED")
        )
        stuck = sum(stages.get(s, {}).get("count", 0) for s in ("COLD_LEAD", "CONTACTED"))
        underperformers = [p for p in snapshot["perf"] if p["target"] and p["conversion"] < 50][:3]
        lines = [
            "**Where revenue is being lost** _(from live CRM data)_",
            "",
            f"• **Lost deals:** {totals['lost']} worth {_inr(lost_value)} — closed-lost pipeline you already invested in.",
            f"• **Unbilled pipeline:** {_inr(pipeline)} open vs {_inr(revenue)} billed — "
            f"{_inr(max(pipeline - revenue, 0))} still sitting in the funnel.",
            f"• **Early-stage drag:** {_inr(early)} in Cold/Contacted/Interested — {stuck} deals may need manager push or disqualification.",
        ]
        if overdue:
            lines.append(f"• **Follow-up gaps:** {overdue} overdue follow-ups — warm leads going cold.")
        if underperformers:
            lines.append("")
            lines.append("**Under-target reps**")
            for p in underperformers:
                gap = max(p["target"] - p["actual"], 0)
                lines.append(f"• {p['name']} ({p['area']}): {p['conversion']}% of target — {_inr(gap)} short")
        lines.extend([
            "",
            "**Recommended actions**",
            "1. Review all LOST deals this month — capture loss reasons and competitor patterns.",
            "2. Escalate overdue follow-ups; assign owner + due date within 48 hours.",
            "3. Focus on NEGOTIATION-stage deals — fastest path from pipeline to billed revenue.",
        ])
        return "\n".join(lines)

    if any(w in q for w in ("pipeline health", "pipeline", "funnel")):
        lines = ["**Pipeline health snapshot**", ""]
        for s in ("COLD_LEAD", "CONTACTED", "INTERESTED", "NEGOTIATION", "WON", "LOST"):
            info = stages.get(s, {"count": 0, "value": 0})
            lines.append(f"• **{s.replace('_', ' ').title()}:** {info['count']} deals · {_inr(info['value'])}")
        lines.append(f"\n**Open pipeline (excl. lost):** {_inr(pipeline)}")
        return "\n".join(lines)

    if any(w in q for w in ("top performer", "best sales", "who are my top")):
        lines = ["**Top performers by target conversion**", ""]
        for i, p in enumerate(snapshot["perf"][:3], 1):
            lines.append(
                f"{i}. **{p['name']}** ({p['area']}) — {_inr(p['actual'])} billed · {p['conversion']}% of target"
            )
        if not snapshot["perf"]:
            lines.append("_No salesperson data in scope yet._")
        return "\n".join(lines)

    return None
