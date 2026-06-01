from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import logging
import uuid
import bcrypt
import jwt as pyjwt
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Literal
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Response, Query
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from springedge import is_configured as springedge_configured, send_message as springedge_send_message

# ---------- App Setup ----------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="Franklin Wardcorpp CRM API")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("crm")

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALG = "HS256"
ROLES = ["ceo", "admin", "sales_manager", "salesperson"]
ROLE_RANK = {"ceo": 4, "admin": 3, "sales_manager": 2, "salesperson": 1}

# ---------- Helpers ----------

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()

def hash_password(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()

def verify_password(p: str, h: str) -> bool:
    try:
        return bcrypt.checkpw(p.encode(), h.encode())
    except Exception:
        return False

def make_token(user_id: str, email: str, role: str, minutes: int = 60 * 24 * 7) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": now_utc() + timedelta(minutes=minutes),
        "type": "access",
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def strip_user(u: dict) -> dict:
    u = dict(u)
    u.pop("password_hash", None)
    u.pop("_id", None)
    return u

async def get_user_from_token(token: str) -> Optional[dict]:
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        user = await db.users.find_one({"id": payload["sub"]})
        return user
    except Exception:
        return None

async def get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "Not authenticated")
    user = await get_user_from_token(token)
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user

def require_roles(*roles):
    async def dep(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(403, f"Requires role: {roles}")
        return user
    return dep

# ---------- Models ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: Literal["ceo", "admin", "sales_manager", "salesperson"]
    designation: Optional[str] = None
    phone: Optional[str] = None
    area: Optional[str] = None
    target: Optional[float] = 0
    reporting_manager_id: Optional[str] = None
    photo_url: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    area: Optional[str] = None
    target: Optional[float] = None
    reporting_manager_id: Optional[str] = None
    photo_url: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None

class LoginBody(BaseModel):
    email: EmailStr
    password: str

class VisitCreate(BaseModel):
    client_name: str
    client_type: Literal["Fabricator", "Transporter", "Dealer", "PSU", "Other"]
    location_text: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    remarks: Optional[str] = ""
    status: Literal["Completed", "Follow-up", "Converted"] = "Completed"

class POCCreate(BaseModel):
    visit_id: Optional[str] = None
    client_name: str
    poc_name: str
    designation: Optional[str] = ""
    mobile: str
    email: Optional[str] = ""
    whatsapp: Optional[str] = ""
    best_time: Optional[str] = ""
    preferred_method: Literal["Call", "WhatsApp", "Email", "Visit"] = "Call"
    notes: Optional[str] = ""
    area: Optional[str] = ""
    client_type: Optional[str] = "Other"

class FollowUpCreate(BaseModel):
    poc_id: str
    due_date: str  # ISO date
    notes: Optional[str] = ""

class FollowUpLog(BaseModel):
    action: Literal["Called", "Visited", "Email Sent", "WhatsApp Sent", "No Response"]
    notes: Optional[str] = ""

class DealCreate(BaseModel):
    client_name: str
    client_type: str
    area: Optional[str] = ""
    poc_id: Optional[str] = None
    poc_name: Optional[str] = ""
    poc_contact: Optional[str] = ""
    estimated_value: float = 0
    stage: Literal["COLD_LEAD", "CONTACTED", "INTERESTED", "NEGOTIATION", "WON", "LOST"] = "COLD_LEAD"
    next_follow_up: Optional[str] = None
    notes: Optional[str] = ""

class DealUpdate(BaseModel):
    stage: Optional[str] = None
    estimated_value: Optional[float] = None
    next_follow_up: Optional[str] = None
    notes: Optional[str] = None
    lost_reason: Optional[str] = None
    client_name: Optional[str] = None
    area: Optional[str] = None

class ProductCreate(BaseModel):
    name: str
    sku: str
    unit_price: float
    category: str
    gst_percent: float = 18

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    unit_price: Optional[float] = None
    category: Optional[str] = None
    gst_percent: Optional[float] = None

class BillLine(BaseModel):
    product_id: str
    product_name: str
    sku: str
    quantity: float
    unit_price: float
    gst_percent: float

class BillCreate(BaseModel):
    client_name: str
    visit_id: Optional[str] = None
    deal_id: Optional[str] = None
    lines: List[BillLine]
    discount_percent: float = 0
    notes: Optional[str] = ""

# ---------- Startup: Seed CEO + Indexes ----------

@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.visits.create_index("salesperson_id")
    await db.pocs.create_index("salesperson_id")
    await db.followups.create_index([("salesperson_id", 1), ("due_date", 1)])
    await db.deals.create_index([("salesperson_id", 1), ("stage", 1)])
    await db.products.create_index("sku", unique=True)
    await db.bills.create_index("salesperson_id")
    await db.notifications.create_index([("user_id", 1), ("read", 1)])

    ceo_email = os.environ.get("ADMIN_EMAIL", "ceo@franklinwardcorpp.com")
    ceo_password = os.environ.get("ADMIN_PASSWORD", "ceo12345")
    existing = await db.users.find_one({"email": ceo_email})
    if not existing:
        ceo = {
            "id": str(uuid.uuid4()),
            "email": ceo_email,
            "password_hash": hash_password(ceo_password),
            "name": "Founder CEO",
            "role": "ceo",
            "designation": "CEO",
            "phone": "+91-9999999999",
            "area": "HQ",
            "target": 0,
            "reporting_manager_id": None,
            "photo_url": "",
            "created_at": iso(now_utc()),
        }
        await db.users.insert_one(ceo)
        logger.info(f"Seeded CEO: {ceo_email}")
        # Seed sample data
        await seed_sample_data(ceo["id"])

async def seed_sample_data(ceo_id: str):
    """Seed demo admin, manager, salespeople + sample products + a few deals."""
    admin = {
        "id": str(uuid.uuid4()), "email": "admin@franklinwardcorpp.com",
        "password_hash": hash_password("admin123"), "name": "Ravi Admin", "role": "admin",
        "designation": "Operations Admin", "phone": "+91-9000000001",
        "area": "North", "target": 0, "reporting_manager_id": ceo_id,
        "photo_url": "", "created_at": iso(now_utc()),
    }
    manager = {
        "id": str(uuid.uuid4()), "email": "manager@franklinwardcorpp.com",
        "password_hash": hash_password("manager123"), "name": "Priya Manager", "role": "sales_manager",
        "designation": "North Zone Manager", "phone": "+91-9000000002",
        "area": "North", "target": 2500000, "reporting_manager_id": admin["id"],
        "photo_url": "", "created_at": iso(now_utc()),
    }
    sp1 = {
        "id": str(uuid.uuid4()), "email": "sales1@franklinwardcorpp.com",
        "password_hash": hash_password("sales123"), "name": "Arjun Field", "role": "salesperson",
        "designation": "Field Sales Executive", "phone": "+91-9000000003",
        "area": "Delhi NCR", "target": 800000, "reporting_manager_id": manager["id"],
        "photo_url": "", "created_at": iso(now_utc()),
    }
    sp2 = {
        "id": str(uuid.uuid4()), "email": "sales2@franklinwardcorpp.com",
        "password_hash": hash_password("sales123"), "name": "Sneha Field", "role": "salesperson",
        "designation": "Field Sales Executive", "phone": "+91-9000000004",
        "area": "Mumbai", "target": 750000, "reporting_manager_id": manager["id"],
        "photo_url": "", "created_at": iso(now_utc()),
    }
    await db.users.insert_many([admin, manager, sp1, sp2])

    products = [
        {"id": str(uuid.uuid4()), "name": "Industrial Bolt M16", "sku": "FW-BLT-M16", "unit_price": 45, "category": "Fasteners", "gst_percent": 18, "created_at": iso(now_utc())},
        {"id": str(uuid.uuid4()), "name": "Hex Nut M20", "sku": "FW-NUT-M20", "unit_price": 32, "category": "Fasteners", "gst_percent": 18, "created_at": iso(now_utc())},
        {"id": str(uuid.uuid4()), "name": "Steel Plate 6mm", "sku": "FW-PLT-6", "unit_price": 1850, "category": "Plates", "gst_percent": 18, "created_at": iso(now_utc())},
        {"id": str(uuid.uuid4()), "name": "Welding Rod 3mm", "sku": "FW-WLD-3", "unit_price": 280, "category": "Consumables", "gst_percent": 18, "created_at": iso(now_utc())},
        {"id": str(uuid.uuid4()), "name": "Grinding Wheel 7in", "sku": "FW-GRD-7", "unit_price": 95, "category": "Consumables", "gst_percent": 18, "created_at": iso(now_utc())},
    ]
    await db.products.insert_many(products)

    from seeds_demo_data import seed_lively_demo
    lively = await seed_lively_demo(db, replace=True)
    if lively.get("ok"):
        logger.info(f"Lively demo data: {lively.get('counts')}")

    from seeds_whatsapp import seed_whatsapp_samples
    wa = await seed_whatsapp_samples(db)
    if wa.get("ok"):
        logger.info(f"WhatsApp demo data: {wa['pocs']} POCs, {wa['followups']} follow-ups for {wa['salesperson']}")

    logger.info("Sample seed data inserted.")

# ---------- SpringEdge messaging ----------

async def springedge_send(to: str, message: str, channel: str = "sms") -> dict:
    try:
        result = await springedge_send_message(to, message, channel)
        status = result.get("status", "unknown")
    except Exception as e:
        logger.exception("SpringEdge send failed")
        err = str(e)
        if len(err) > 200 or "HTTPSConnectionPool" in err:
            err = "Could not reach SpringEdge. Check API key, sender ID, and network."
        result = {"status": "failed", "error": err, "channel": channel, "to": to}
        status = "failed"
    doc = {
        "id": str(uuid.uuid4()),
        "to": to,
        "message": message,
        "channel": channel,
        "status": status,
        "detail": result,
        "sent_at": iso(now_utc()),
    }
    await db.sms_logs.insert_one(doc)
    return result

async def push_notification(user_id: str, title: str, body: str, kind: str = "info"):
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()), "user_id": user_id, "title": title,
        "body": body, "kind": kind, "read": False, "created_at": iso(now_utc())
    })

# ---------- AUTH ----------

@api.post("/auth/login")
async def login(body: LoginBody, response: Response):
    user = await db.users.find_one({"email": body.email.lower()})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    token = make_token(user["id"], user["email"], user["role"])
    response.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 7, path="/")
    return {"token": token, "user": strip_user(user)}

@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}

@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return strip_user(user)

# ---------- USERS / EMPLOYEES ----------

def can_manage(actor_role: str, target_role: str) -> bool:
    return ROLE_RANK[actor_role] > ROLE_RANK[target_role]

@api.post("/users")
async def create_user(body: UserCreate, actor: dict = Depends(get_current_user)):
    if not can_manage(actor["role"], body.role):
        raise HTTPException(403, "Insufficient role to create this user")
    existing = await db.users.find_one({"email": body.email.lower()})
    if existing:
        raise HTTPException(400, "Email already exists")
    new_user = {
        "id": str(uuid.uuid4()),
        "email": body.email.lower(),
        "password_hash": hash_password(body.password),
        "name": body.name, "role": body.role,
        "designation": body.designation or "",
        "phone": body.phone or "",
        "area": body.area or "",
        "target": body.target or 0,
        "reporting_manager_id": body.reporting_manager_id or actor["id"],
        "photo_url": body.photo_url or "",
        "created_at": iso(now_utc()),
    }
    await db.users.insert_one(new_user)
    return strip_user(new_user)

@api.get("/users")
async def list_users(actor: dict = Depends(get_current_user), role: Optional[str] = None):
    query = {}
    if role:
        query["role"] = role
    if actor["role"] == "salesperson":
        query["id"] = actor["id"]
    elif actor["role"] == "sales_manager":
        query["$or"] = [{"reporting_manager_id": actor["id"]}, {"id": actor["id"]}]
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api.get("/users/{user_id}")
async def get_user(user_id: str, actor: dict = Depends(get_current_user)):
    u = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not u:
        raise HTTPException(404, "Not found")
    return u

@api.patch("/users/{user_id}")
async def update_user(user_id: str, body: UserUpdate, actor: dict = Depends(get_current_user)):
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(404, "Not found")
    if target["id"] != actor["id"] and not can_manage(actor["role"], target["role"]):
        raise HTTPException(403, "Cannot edit this user")
    update = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if "password" in update:
        update["password_hash"] = hash_password(update.pop("password"))
    if update:
        await db.users.update_one({"id": user_id}, {"$set": update})
    new = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    return new

@api.delete("/users/{user_id}")
async def delete_user(user_id: str, actor: dict = Depends(require_roles("ceo", "admin"))):
    if actor["id"] == user_id:
        raise HTTPException(400, "Cannot delete self")
    await db.users.delete_one({"id": user_id})
    return {"ok": True}

# ---------- VISITS ----------

async def get_team_ids(actor: dict) -> List[str]:
    """For sales_manager: direct reports + self."""
    direct = await db.users.find({"reporting_manager_id": actor["id"]}, {"id": 1, "_id": 0}).to_list(500)
    ids = [u["id"] for u in direct] + [actor["id"]]
    return ids

def scoped_user_filter(actor: dict, field: str = "salesperson_id"):
    """Return mongo filter for visibility scope. (Sync — for salesperson only.)"""
    if actor["role"] == "salesperson":
        return {field: actor["id"]}
    return {}

async def scoped_user_filter_async(actor: dict, field: str = "salesperson_id"):
    """Role-aware visibility. salesperson -> self; sales_manager -> team; ceo/admin -> all."""
    if actor["role"] == "salesperson":
        return {field: actor["id"]}
    if actor["role"] == "sales_manager":
        ids = await get_team_ids(actor)
        return {field: {"$in": ids}}
    return {}

@api.post("/visits")
async def create_visit(body: VisitCreate, actor: dict = Depends(get_current_user)):
    doc = body.model_dump()
    doc.update({
        "id": str(uuid.uuid4()),
        "salesperson_id": actor["id"],
        "salesperson_name": actor["name"],
        "visit_date": iso(now_utc()),
        "created_at": iso(now_utc()),
    })
    await db.visits.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.get("/visits")
async def list_visits(actor: dict = Depends(get_current_user),
                      salesperson_id: Optional[str] = None,
                      client_type: Optional[str] = None,
                      status: Optional[str] = None):
    q = await scoped_user_filter_async(actor)
    if salesperson_id and actor["role"] != "salesperson":
        q["salesperson_id"] = salesperson_id
    if client_type:
        q["client_type"] = client_type
    if status:
        q["status"] = status
    visits = await db.visits.find(q, {"_id": 0}).sort("visit_date", -1).to_list(2000)
    return visits

# ---------- POCs ----------

@api.post("/pocs")
async def create_poc(body: POCCreate, actor: dict = Depends(get_current_user)):
    doc = body.model_dump()
    doc.update({
        "id": str(uuid.uuid4()),
        "salesperson_id": actor["id"],
        "salesperson_name": actor["name"],
        "created_at": iso(now_utc()),
    })
    await db.pocs.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.get("/pocs")
async def list_pocs(actor: dict = Depends(get_current_user), area: Optional[str] = None):
    q = await scoped_user_filter_async(actor)
    if area:
        q["area"] = area
    pocs = await db.pocs.find(q, {"_id": 0}).sort("created_at", -1).to_list(2000)
    return pocs

# ---------- Follow-ups ----------

@api.post("/followups")
async def create_followup(body: FollowUpCreate, actor: dict = Depends(get_current_user)):
    poc = await db.pocs.find_one({"id": body.poc_id})
    if not poc:
        raise HTTPException(404, "POC not found")
    doc = {
        "id": str(uuid.uuid4()),
        "poc_id": body.poc_id,
        "poc_name": poc.get("poc_name"),
        "client_name": poc.get("client_name"),
        "salesperson_id": actor["id"],
        "salesperson_name": actor["name"],
        "due_date": body.due_date,
        "notes": body.notes or "",
        "status": "pending",
        "logs": [],
        "escalated": False,
        "created_at": iso(now_utc()),
    }
    await db.followups.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.get("/followups")
async def list_followups(actor: dict = Depends(get_current_user),
                         status_filter: Optional[str] = Query(None),
                         scope: Optional[str] = Query("mine")):
    q = {}
    if scope == "mine" or actor["role"] == "salesperson":
        q["salesperson_id"] = actor["id"]
    if status_filter:
        q["status"] = status_filter
    flws = await db.followups.find(q, {"_id": 0}).sort("due_date", 1).to_list(2000)
    # Tag overdue
    today = now_utc().date().isoformat()
    for f in flws:
        try:
            due = f["due_date"][:10]
            if due < today and f["status"] == "pending":
                f["is_overdue"] = True
            else:
                f["is_overdue"] = False
        except Exception:
            f["is_overdue"] = False
    return flws

@api.post("/followups/{fid}/log")
async def log_followup(fid: str, body: FollowUpLog, actor: dict = Depends(get_current_user)):
    f = await db.followups.find_one({"id": fid})
    if not f:
        raise HTTPException(404, "Not found")
    log = {
        "action": body.action,
        "notes": body.notes or "",
        "at": iso(now_utc()),
        "by": actor["name"],
    }
    new_status = "completed" if body.action in ("Called", "Visited", "Email Sent", "WhatsApp Sent") else "pending"
    await db.followups.update_one(
        {"id": fid},
        {"$push": {"logs": log}, "$set": {"status": new_status, "last_action_at": iso(now_utc())}}
    )
    messaging = None
    if body.action == "WhatsApp Sent":
        phone = ""
        if f.get("poc_id"):
            poc = await db.pocs.find_one({"id": f["poc_id"]})
            if poc:
                phone = (poc.get("whatsapp") or poc.get("mobile") or "").strip()
        text = body.notes or f"Follow-up from {actor['name']} re: {f.get('client_name', 'your account')}"
        messaging = await springedge_send(phone or f.get("poc_name", ""), text, "whatsapp")
    return {"ok": True, "log": log, "messaging": messaging}

@api.post("/followups/escalate-overdue")
async def escalate_overdue(actor: dict = Depends(require_roles("ceo", "admin", "sales_manager"))):
    today = now_utc().date().isoformat()
    cursor = db.followups.find({"status": "pending", "escalated": False, "due_date": {"$lt": today}})
    count = 0
    async for f in cursor:
        sp = await db.users.find_one({"id": f["salesperson_id"]})
        if sp and sp.get("reporting_manager_id"):
            mgr = await db.users.find_one({"id": sp["reporting_manager_id"]})
            if mgr:
                await push_notification(mgr["id"], "Overdue Follow-up Escalation",
                                        f"{sp['name']} missed follow-up with {f.get('client_name')} ({f.get('poc_name')})",
                                        "warning")
                await springedge_send(
                    mgr.get("phone", ""),
                    f"Escalation: {sp['name']} missed follow-up with {f.get('client_name')} ({f.get('poc_name')})",
                    "sms",
                )
        await db.followups.update_one({"id": f["id"]}, {"$set": {"escalated": True}})
        count += 1
    return {"escalated": count}

# ---------- DEALS / KANBAN ----------

@api.post("/deals")
async def create_deal(body: DealCreate, actor: dict = Depends(get_current_user)):
    doc = body.model_dump()
    doc.update({
        "id": str(uuid.uuid4()),
        "salesperson_id": actor["id"],
        "salesperson_name": actor["name"],
        "touchpoints": 0,
        "last_contacted": iso(now_utc()),
        "created_at": iso(now_utc()),
    })
    await db.deals.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.get("/deals")
async def list_deals(actor: dict = Depends(get_current_user),
                     salesperson_id: Optional[str] = None,
                     area: Optional[str] = None,
                     client_type: Optional[str] = None,
                     stage: Optional[str] = None):
    q = await scoped_user_filter_async(actor)
    if salesperson_id and actor["role"] != "salesperson":
        q["salesperson_id"] = salesperson_id
    if area:
        q["area"] = area
    if client_type:
        q["client_type"] = client_type
    if stage:
        q["stage"] = stage
    return await db.deals.find(q, {"_id": 0}).sort("created_at", -1).to_list(2000)

@api.patch("/deals/{deal_id}")
async def update_deal(deal_id: str, body: DealUpdate, actor: dict = Depends(get_current_user)):
    deal = await db.deals.find_one({"id": deal_id})
    if not deal:
        raise HTTPException(404, "Not found")
    update = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    update["last_contacted"] = iso(now_utc())
    update["touchpoints"] = deal.get("touchpoints", 0) + 1
    await db.deals.update_one({"id": deal_id}, {"$set": update})
    new = await db.deals.find_one({"id": deal_id}, {"_id": 0})
    # Notify if WON: hint billing
    if body.stage == "WON":
        await push_notification(deal["salesperson_id"], "Deal Won 🎉",
                                f"{deal['client_name']} moved to WON. Create invoice.", "success")
    return new

@api.delete("/deals/{deal_id}")
async def delete_deal(deal_id: str, actor: dict = Depends(get_current_user)):
    await db.deals.delete_one({"id": deal_id})
    return {"ok": True}

# ---------- PRODUCTS ----------

@api.post("/products")
async def create_product(body: ProductCreate, actor: dict = Depends(require_roles("ceo", "admin"))):
    if await db.products.find_one({"sku": body.sku}):
        raise HTTPException(400, "SKU exists")
    doc = body.model_dump()
    doc.update({"id": str(uuid.uuid4()), "created_at": iso(now_utc())})
    await db.products.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.get("/products")
async def list_products(actor: dict = Depends(get_current_user)):
    return await db.products.find({}, {"_id": 0}).sort("name", 1).to_list(1000)

@api.patch("/products/{pid}")
async def update_product(pid: str, body: ProductUpdate, actor: dict = Depends(require_roles("ceo", "admin"))):
    update = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if update:
        await db.products.update_one({"id": pid}, {"$set": update})
    return await db.products.find_one({"id": pid}, {"_id": 0})

@api.delete("/products/{pid}")
async def delete_product(pid: str, actor: dict = Depends(require_roles("ceo", "admin"))):
    await db.products.delete_one({"id": pid})
    return {"ok": True}

# ---------- BILLS ----------

@api.post("/bills")
async def create_bill(body: BillCreate, actor: dict = Depends(get_current_user)):
    subtotal = 0.0
    gst_total = 0.0
    line_items = []
    for ln in body.lines:
        line_amount = ln.quantity * ln.unit_price
        line_gst = line_amount * (ln.gst_percent / 100)
        subtotal += line_amount
        gst_total += line_gst
        line_items.append({**ln.model_dump(), "line_amount": round(line_amount, 2), "line_gst": round(line_gst, 2)})
    discount_amount = subtotal * (body.discount_percent / 100)
    grand_total = subtotal - discount_amount + gst_total
    doc = {
        "id": str(uuid.uuid4()),
        "invoice_no": f"FW-{int(now_utc().timestamp())}",
        "client_name": body.client_name,
        "visit_id": body.visit_id,
        "deal_id": body.deal_id,
        "salesperson_id": actor["id"],
        "salesperson_name": actor["name"],
        "lines": line_items,
        "subtotal": round(subtotal, 2),
        "discount_percent": body.discount_percent,
        "discount_amount": round(discount_amount, 2),
        "gst_total": round(gst_total, 2),
        "grand_total": round(grand_total, 2),
        "needs_approval": body.discount_percent > 0,
        "notes": body.notes or "",
        "created_at": iso(now_utc()),
    }
    await db.bills.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.get("/bills")
async def list_bills(actor: dict = Depends(get_current_user),
                     salesperson_id: Optional[str] = None,
                     client_name: Optional[str] = None):
    q = await scoped_user_filter_async(actor)
    if salesperson_id and actor["role"] != "salesperson":
        q["salesperson_id"] = salesperson_id
    if client_name:
        q["client_name"] = {"$regex": client_name, "$options": "i"}
    return await db.bills.find(q, {"_id": 0}).sort("created_at", -1).to_list(2000)

# ---------- DASHBOARD / ANALYTICS ----------

@api.get("/dashboard/overview")
async def dashboard_overview(actor: dict = Depends(get_current_user)):
    q = await scoped_user_filter_async(actor)
    total_visits = await db.visits.count_documents(q)
    total_pocs = await db.pocs.count_documents(q)
    total_deals = await db.deals.count_documents(q)
    won_deals = await db.deals.count_documents({**q, "stage": "WON"})
    lost_deals = await db.deals.count_documents({**q, "stage": "LOST"})
    # pipeline values per stage
    stages_summary = {}
    pipeline_total = 0
    async for d in db.deals.find(q, {"_id": 0, "stage": 1, "estimated_value": 1}):
        s = d.get("stage", "COLD_LEAD")
        stages_summary[s] = stages_summary.get(s, {"count": 0, "value": 0})
        stages_summary[s]["count"] += 1
        stages_summary[s]["value"] += d.get("estimated_value", 0) or 0
        if s not in ("LOST",):
            pipeline_total += d.get("estimated_value", 0) or 0
    # bills total
    bills_total = 0
    bills_count = await db.bills.count_documents(q)
    async for b in db.bills.find(q, {"_id": 0, "grand_total": 1, "created_at": 1}):
        bills_total += b.get("grand_total", 0) or 0
    # monthly revenue trend (12 months)
    months = {}
    today = now_utc()
    for i in range(11, -1, -1):
        m = (today.replace(day=1) - timedelta(days=30 * i)).strftime("%Y-%m")
        months[m] = 0
    async for b in db.bills.find(q, {"_id": 0, "grand_total": 1, "created_at": 1}):
        try:
            ym = b["created_at"][:7]
            if ym in months:
                months[ym] += b["grand_total"]
        except Exception:
            pass
    monthly_revenue = [{"month": k, "revenue": v} for k, v in months.items()]
    return {
        "totals": {
            "visits": total_visits, "pocs": total_pocs, "deals": total_deals,
            "won": won_deals, "lost": lost_deals, "bills": bills_count, "revenue": round(bills_total, 2),
            "pipeline_value": round(pipeline_total, 2),
        },
        "stages_summary": stages_summary,
        "monthly_revenue": monthly_revenue,
    }

@api.get("/dashboard/performance")
async def dashboard_performance(actor: dict = Depends(get_current_user)):
    # Per salesperson card data
    sp_query = {"role": "salesperson"}
    if actor["role"] == "sales_manager":
        sp_query["reporting_manager_id"] = actor["id"]
    if actor["role"] == "salesperson":
        sp_query["id"] = actor["id"]
    salespersons = await db.users.find(sp_query, {"_id": 0, "password_hash": 0}).to_list(500)
    result = []
    for sp in salespersons:
        bills = await db.bills.find({"salesperson_id": sp["id"]}, {"_id": 0}).to_list(5000)
        actual = sum(b.get("grand_total", 0) for b in bills)
        target = sp.get("target", 0) or 0
        conv = (actual / target * 100) if target > 0 else 0
        total_deals = await db.deals.count_documents({"salesperson_id": sp["id"]})
        won_deals = await db.deals.count_documents({"salesperson_id": sp["id"], "stage": "WON"})
        pipeline_conv = (won_deals / total_deals * 100) if total_deals > 0 else 0
        visit_count = await db.visits.count_documents({"salesperson_id": sp["id"]})
        # product breakdown
        product_breakdown = {}
        for b in bills:
            for ln in b.get("lines", []):
                product_breakdown[ln["product_name"]] = product_breakdown.get(ln["product_name"], 0) + ln.get("line_amount", 0)
        result.append({
            "id": sp["id"], "name": sp["name"], "area": sp.get("area", ""),
            "target": target, "actual": round(actual, 2),
            "conversion_rate": round(conv, 1),
            "pipeline_conversion": round(pipeline_conv, 1),
            "visits": visit_count, "deals": total_deals, "won": won_deals,
            "product_breakdown": product_breakdown,
            "photo_url": sp.get("photo_url", ""),
        })
    return result

@api.get("/dashboard/funnel")
async def funnel(actor: dict = Depends(get_current_user)):
    q = await scoped_user_filter_async(actor)
    visits = await db.visits.count_documents(q)
    pocs = await db.pocs.count_documents(q)
    deals = await db.deals.count_documents(q)
    won = await db.deals.count_documents({**q, "stage": "WON"})
    bills_total = 0
    async for b in db.bills.find(q, {"_id": 0, "grand_total": 1}):
        bills_total += b.get("grand_total", 0) or 0
    return {
        "stages": [
            {"label": "Visits", "value": visits},
            {"label": "POCs", "value": pocs},
            {"label": "Pipeline", "value": deals},
            {"label": "Won", "value": won},
        ],
        "billed_value": round(bills_total, 2),
    }

@api.get("/dashboard/agent-locations")
async def agent_locations(actor: dict = Depends(require_roles("ceo", "admin", "sales_manager"))):
    """Return ALL salespeople + managers; pick the most recent of (last visit GPS) vs (last ping) for live tracking."""
    # latest visit lat/lng + timestamp per salesperson
    pipeline = [
        {"$match": {"lat": {"$ne": None}, "lng": {"$ne": None}}},
        {"$sort": {"visit_date": -1}},
        {"$group": {
            "_id": "$salesperson_id",
            "lat": {"$first": "$lat"}, "lng": {"$first": "$lng"},
            "visit_date": {"$first": "$visit_date"},
            "client": {"$first": "$client_name"},
        }},
    ]
    by_visit = {}
    async for d in db.visits.aggregate(pipeline):
        by_visit[d["_id"]] = d

    # Determine which users to show based on role
    if actor["role"] == "sales_manager":
        team = await get_team_ids(actor)
        users = await db.users.find({"id": {"$in": team}, "role": {"$in": ["salesperson", "sales_manager"]}}, {"_id": 0, "password_hash": 0}).to_list(500)
    else:
        users = await db.users.find({"role": {"$in": ["salesperson", "sales_manager"]}}, {"_id": 0, "password_hash": 0}).to_list(500)

    # HQ defaults by area (rough India coords) — fallback if no GPS at all
    area_hq = {
        "Delhi NCR": (28.7041, 77.1025), "Delhi": (28.7041, 77.1025),
        "Mumbai": (19.0760, 72.8777), "Gurugram": (28.4595, 77.0266),
        "Noida": (28.5355, 77.3910), "Bangalore": (12.9716, 77.5946),
        "Bengaluru": (12.9716, 77.5946), "Chennai": (13.0827, 80.2707),
        "Kolkata": (22.5726, 88.3639), "Hyderabad": (17.3850, 78.4867),
        "Pune": (18.5204, 73.8567), "Ahmedabad": (23.0225, 72.5714),
        "North": (28.7041, 77.1025), "South": (12.9716, 77.5946),
        "HQ": (22.5, 78.9),
    }
    out = []
    for u in users:
        visit = by_visit.get(u["id"])
        visit_ts = visit["visit_date"] if visit else None
        ping_ts = u.get("last_ping_at")
        # Pick the most recent source between visit and ping
        use_ping = bool(ping_ts and (not visit_ts or ping_ts > visit_ts))
        if use_ping:
            lat, lng = u["last_ping_lat"], u["last_ping_lng"]
            source = "ping"; last_seen = ping_ts; client = "Live ping"
        elif visit:
            lat, lng = visit["lat"], visit["lng"]
            source = "visit"; last_seen = visit_ts; client = visit.get("client")
        else:
            coord = area_hq.get(u.get("area", ""), area_hq["HQ"])
            offset = (hash(u["id"]) % 100) / 1000.0
            lat, lng = coord[0] + offset, coord[1] + offset
            source = "default"; last_seen = None; client = "No GPS yet"
        out.append({
            "salesperson_id": u["id"], "name": u["name"],
            "role": u["role"], "area": u.get("area", ""),
            "phone": u.get("phone", ""), "photo_url": u.get("photo_url", ""),
            "lat": lat, "lng": lng, "source": source,
            "last_seen": last_seen, "client": client,
        })
    return out

class PingLocationBody(BaseModel):
    lat: float
    lng: float

@api.post("/users/me/ping-location")
async def ping_location(body: PingLocationBody, actor: dict = Depends(get_current_user)):
    """Broadcast current GPS so manager sees salesperson on map without a visit."""
    await db.users.update_one(
        {"id": actor["id"]},
        {"$set": {"last_ping_lat": body.lat, "last_ping_lng": body.lng, "last_ping_at": iso(now_utc())}}
    )
    return {"ok": True}

@api.get("/dashboard/top-products")
async def top_products(actor: dict = Depends(get_current_user)):
    q = await scoped_user_filter_async(actor)
    breakdown = {}
    async for b in db.bills.find(q, {"_id": 0, "lines": 1}):
        for ln in b.get("lines", []):
            key = ln["product_name"]
            breakdown[key] = breakdown.get(key, 0) + ln.get("line_amount", 0)
    items = [{"name": k, "value": round(v, 2)} for k, v in sorted(breakdown.items(), key=lambda x: -x[1])[:10]]
    return items

# ---------- NOTIFICATIONS ----------

@api.get("/messaging/status")
async def messaging_status(actor: dict = Depends(get_current_user)):
    return {
        "configured": springedge_configured(),
        "channels": ["sms", "whatsapp"],
    }

class MessagingTestBody(BaseModel):
    to: str
    message: str = "Franklin Wardcorpp CRM test message"
    channel: Literal["sms", "whatsapp"] = "sms"

@api.post("/messaging/test")
async def messaging_test(body: MessagingTestBody, actor: dict = Depends(require_roles("ceo", "admin"))):
    """Send a test message (admin/CEO only)."""
    result = await springedge_send(body.to, body.message, body.channel)
    return result

@api.post("/dev/seed-whatsapp-samples")
async def dev_seed_whatsapp_samples(actor: dict = Depends(require_roles("ceo", "admin"))):
    """Insert POCs + follow-ups for SpringEdge WhatsApp testing (replaces prior demo rows)."""
    from seeds_whatsapp import seed_whatsapp_samples
    return await seed_whatsapp_samples(db)

@api.post("/dev/seed-demo-data")
async def dev_seed_demo_data(
    replace: bool = Query(True, description="Replace prior lively_demo rows"),
    actor: dict = Depends(require_roles("ceo", "admin")),
):
    """Populate visits, POCs, follow-ups, pipeline, bills, notifications for a lively UI."""
    from seeds_demo_data import seed_lively_demo
    return await seed_lively_demo(db, replace=replace)

@api.get("/notifications")
async def list_notifications(actor: dict = Depends(get_current_user)):
    return await db.notifications.find({"user_id": actor["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)

@api.post("/notifications/{nid}/read")
async def mark_read(nid: str, actor: dict = Depends(get_current_user)):
    await db.notifications.update_one({"id": nid, "user_id": actor["id"]}, {"$set": {"read": True}})
    return {"ok": True}

@api.post("/notifications/mark-all-read")
async def mark_all_read(actor: dict = Depends(get_current_user)):
    await db.notifications.update_many({"user_id": actor["id"]}, {"$set": {"read": True}})
    return {"ok": True}

# ---------- REPORTS (return JSON; frontend exports to PDF/Excel) ----------

@api.get("/reports/visits")
async def report_visits(actor: dict = Depends(get_current_user)):
    q = await scoped_user_filter_async(actor)
    return await db.visits.find(q, {"_id": 0}).sort("visit_date", -1).to_list(5000)

@api.get("/reports/bills")
async def report_bills(actor: dict = Depends(get_current_user)):
    q = await scoped_user_filter_async(actor)
    return await db.bills.find(q, {"_id": 0}).sort("created_at", -1).to_list(5000)

@api.get("/reports/pipeline")
async def report_pipeline(actor: dict = Depends(get_current_user)):
    q = await scoped_user_filter_async(actor)
    return await db.deals.find(q, {"_id": 0}).sort("created_at", -1).to_list(5000)

@api.get("/reports/pocs")
async def report_pocs(actor: dict = Depends(get_current_user)):
    q = await scoped_user_filter_async(actor)
    return await db.pocs.find(q, {"_id": 0}).sort("created_at", -1).to_list(5000)

# ---------- AI CHATBOT (Claude Sonnet 4.5) ----------

class ChatAskBody(BaseModel):
    session_id: Optional[str] = None
    message: str

async def build_crm_context(actor: dict) -> str:
    """Snapshot of CRM facts injected into Claude system prompt."""
    q = await scoped_user_filter_async(actor)
    total_visits = await db.visits.count_documents(q)
    total_pocs = await db.pocs.count_documents(q)
    total_deals = await db.deals.count_documents(q)
    won = await db.deals.count_documents({**q, "stage": "WON"})
    lost = await db.deals.count_documents({**q, "stage": "LOST"})
    # Stage pipeline
    stage_summary = {}
    pipeline_total = 0
    async for d in db.deals.find(q, {"_id": 0, "stage": 1, "estimated_value": 1, "client_name": 1, "salesperson_name": 1}):
        s = d.get("stage", "?")
        stage_summary[s] = stage_summary.get(s, {"count": 0, "value": 0})
        stage_summary[s]["count"] += 1
        stage_summary[s]["value"] += d.get("estimated_value", 0) or 0
        if s != "LOST":
            pipeline_total += d.get("estimated_value", 0) or 0
    # Revenue
    bills = await db.bills.find(q, {"_id": 0, "grand_total": 1, "client_name": 1, "salesperson_name": 1, "created_at": 1, "lines": 1}).to_list(500)
    revenue = sum(b.get("grand_total", 0) for b in bills)
    # Top performers
    sp_q = {"role": "salesperson"}
    if actor["role"] == "sales_manager":
        sp_q["reporting_manager_id"] = actor["id"]
    salespeople = await db.users.find(sp_q, {"_id": 0, "password_hash": 0}).to_list(500)
    perf = []
    for sp in salespeople:
        sp_bills = [b for b in bills if b.get("salesperson_name") == sp["name"]]
        actual = sum(b.get("grand_total", 0) for b in sp_bills)
        target = sp.get("target", 0) or 0
        perf.append({
            "name": sp["name"], "area": sp.get("area", ""),
            "target": target, "actual": round(actual, 2),
            "conversion": round((actual / target * 100) if target else 0, 1),
        })
    perf.sort(key=lambda x: -x["conversion"])
    # Top products
    prod = {}
    for b in bills:
        for ln in b.get("lines", []):
            prod[ln["product_name"]] = prod.get(ln["product_name"], 0) + ln.get("line_amount", 0)
    top_products = sorted(prod.items(), key=lambda x: -x[1])[:5]
    # Overdue followups
    today = now_utc().date().isoformat()
    overdue_q = {**q, "status": "pending", "due_date": {"$lt": today}} if q else {"status": "pending", "due_date": {"$lt": today}}
    overdue = await db.followups.count_documents(overdue_q)

    lines = [
        f"COMPANY: Franklin Wardcorpp (Industrial Fasteners & Steel — India)",
        f"USER: {actor['name']} ({actor['role']})",
        f"SCOPE: {'team-wide' if actor['role'] in ('ceo','admin') else 'own team' if actor['role']=='sales_manager' else 'self'}",
        "",
        f"== TOTALS ==",
        f"Visits: {total_visits} · POCs: {total_pocs} · Deals: {total_deals} (WON: {won}, LOST: {lost})",
        f"Pipeline value (excl. lost): ₹{pipeline_total:,.0f}",
        f"Total billed revenue: ₹{revenue:,.0f}",
        f"Overdue follow-ups: {overdue}",
        "",
        f"== KANBAN STAGES ==",
    ]
    for s, info in stage_summary.items():
        lines.append(f"  {s}: {info['count']} deals · ₹{info['value']:,.0f}")
    lines.append("")
    lines.append(f"== SALESPEOPLE PERFORMANCE (sorted by conversion) ==")
    for p in perf[:10]:
        lines.append(f"  {p['name']} ({p['area']}): ₹{p['actual']:,.0f} / target ₹{p['target']:,.0f} · {p['conversion']}%")
    lines.append("")
    lines.append(f"== TOP PRODUCTS BY REVENUE ==")
    for name, val in top_products:
        lines.append(f"  {name}: ₹{val:,.0f}")
    return "\n".join(lines)

@api.get("/ai/status")
async def ai_status(actor: dict = Depends(require_roles("ceo", "admin", "sales_manager"))):
    from llm_provider import status as llm_status
    return llm_status()

@api.post("/ai/ask")
async def ai_ask(body: ChatAskBody, actor: dict = Depends(require_roles("ceo", "admin", "sales_manager"))):
    from llm_provider import complete_chat, is_configured

    if not is_configured():
        raise HTTPException(
            500,
            "LLM not configured. Set BEDROCK_API_KEY, BEDROCK_MODEL_ID, and AWS_REGION in backend/.env",
        )

    session_id = body.session_id or str(uuid.uuid4())
    context = await build_crm_context(actor)
    system = (
        "You are FRANKLIN-AI, a sharp, concise sales-intelligence analyst for the Franklin Wardcorpp executive team. "
        "You answer questions about the CRM data shown below. Be direct, cite numbers, surface anomalies, and recommend actions. "
        "Use rupees (₹) and short bullet points. Never invent numbers — if a metric isn't in the context, say so.\n\n"
        f"=== LIVE CRM SNAPSHOT ===\n{context}\n=== END SNAPSHOT ==="
    )

    prior = await db.chat_messages.find(
        {"session_id": session_id, "user_id": actor["id"]}, {"_id": 0}
    ).sort("ts", 1).to_list(50)

    try:
        reply = await complete_chat(system, prior, body.message)
    except Exception as e:
        logger.exception("LLM error")
        raise HTTPException(500, str(e))

    now = iso(now_utc())
    await db.chat_messages.insert_many([
        {"id": str(uuid.uuid4()), "session_id": session_id, "user_id": actor["id"], "role": "user", "text": body.message, "ts": now},
        {"id": str(uuid.uuid4()), "session_id": session_id, "user_id": actor["id"], "role": "assistant", "text": str(reply), "ts": iso(now_utc())},
    ])
    return {"session_id": session_id, "reply": str(reply)}

@api.get("/ai/sessions")
async def ai_sessions(actor: dict = Depends(get_current_user)):
    pipeline = [
        {"$match": {"user_id": actor["id"]}},
        {"$sort": {"ts": -1}},
        {"$group": {"_id": "$session_id", "last_ts": {"$first": "$ts"}, "preview": {"$first": "$text"}}},
        {"$sort": {"last_ts": -1}},
        {"$limit": 20},
    ]
    sessions = []
    async for s in db.chat_messages.aggregate(pipeline):
        sessions.append({"session_id": s["_id"], "last_ts": s["last_ts"], "preview": (s["preview"] or "")[:80]})
    return sessions

@api.get("/ai/sessions/{session_id}/messages")
async def ai_messages(session_id: str, actor: dict = Depends(get_current_user)):
    return await db.chat_messages.find(
        {"session_id": session_id, "user_id": actor["id"]}, {"_id": 0}
    ).sort("ts", 1).to_list(200)

# ---------- OVERVIEW REPORT (full executive snapshot for PDF) ----------

@api.get("/reports/overview")
async def report_overview(actor: dict = Depends(get_current_user)):
    """Bundle every chart-ready dataset for the beautiful PDF."""
    q = await scoped_user_filter_async(actor)
    overview = await dashboard_overview(actor)  # reuse
    perf = await dashboard_performance(actor)
    funnel_data = await funnel(actor)
    top = await top_products(actor)
    # Recent bills sample
    recent_bills = await db.bills.find(q, {"_id": 0}).sort("created_at", -1).to_list(5)
    return {
        "generated_at": iso(now_utc()),
        "actor": {"name": actor["name"], "role": actor["role"]},
        "overview": overview,
        "performance": perf,
        "funnel": funnel_data,
        "top_products": top,
        "recent_bills": recent_bills,
    }

# ---------- Mount ----------

@api.get("/")
async def root():
    return {"message": "Franklin Wardcorpp CRM API", "version": "1.0"}

app.include_router(api)

_cors_env = os.environ.get("CORS_ORIGINS", "").strip()
if _cors_env:
    _cors_kw = {"allow_origins": [o.strip() for o in _cors_env.split(",") if o.strip()]}
else:
    # Local dev: allow any localhost port (3000, 3001, …)
    _cors_kw = {"allow_origin_regex": r"https?://(localhost|127\.0\.0\.1)(:\d+)?"}
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    **_cors_kw,
)
