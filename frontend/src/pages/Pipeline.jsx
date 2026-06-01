import React, { useEffect, useState } from "react";
import {
  DndContext, closestCenter, PointerSensor, useSensor, useSensors, useDraggable, useDroppable,
} from "@dnd-kit/core";
import api from "../lib/api";
import { PageHeader, EmptyState, StatCard } from "../components/Common";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "../components/ui/sheet";
import { Badge } from "../components/ui/badge";
import { Plus, ArrowsOutCardinal } from "@phosphor-icons/react";
import { toast } from "sonner";
import { formatINR, formatDate, daysUntil, stageMeta } from "../lib/format";
import { useAuth } from "../context/AuthContext";

const STAGES = ["COLD_LEAD", "CONTACTED", "INTERESTED", "NEGOTIATION", "WON", "LOST"];

export default function Pipeline() {
  const { user } = useAuth();
  const [deals, setDeals] = useState([]);
  const [open, setOpen] = useState(false);
  const [salespersons, setSalespersons] = useState([]);
  const [filters, setFilters] = useState({ salesperson_id: "", area: "", client_type: "" });

  const load = async () => {
    const params = {};
    Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v; });
    const { data } = await api.get("/deals", { params });
    setDeals(data);
  };

  useEffect(() => { load(); }, [filters]);
  useEffect(() => {
    if (["ceo","admin","sales_manager"].includes(user.role)) {
      api.get("/users", { params: { role: "salesperson" } }).then((r) => setSalespersons(r.data));
    }
  }, [user.role]);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  const onDragEnd = async (e) => {
    const overId = e.over?.id;
    const dealId = e.active?.id;
    if (!overId || !dealId) return;
    const deal = deals.find((d) => d.id === dealId);
    if (!deal || deal.stage === overId) return;
    setDeals((d) => d.map((x) => (x.id === dealId ? { ...x, stage: overId } : x)));
    try {
      await api.patch(`/deals/${dealId}`, { stage: overId });
      toast.success(`Moved to ${stageMeta[overId].label}`);
      if (overId === "WON") toast.message("🎉 Won! Create invoice from Bills page.");
      load();
    } catch {
      toast.error("Failed to move");
      load();
    }
  };

  const totals = STAGES.map((s) => {
    const arr = deals.filter((d) => d.stage === s);
    return { stage: s, count: arr.length, value: arr.reduce((a, b) => a + (b.estimated_value || 0), 0) };
  });

  return (
    <div>
      <PageHeader
        overline="Module 3"
        title="Deal Pipeline"
        subtitle="Drag cards between stages. Color-coded follow-up dates highlight urgency."
        actions={
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button data-testid="new-deal-btn"><Plus size={16} className="mr-1.5" weight="bold" /> New Deal</Button>
            </SheetTrigger>
            <SheetContent className="overflow-y-auto w-full sm:max-w-lg">
              <DealForm onClose={() => { setOpen(false); load(); }} />
            </SheetContent>
          </Sheet>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-6">
        {totals.map((t) => (
          <StatCard key={t.stage} label={stageMeta[t.stage].label} value={t.count} sub={formatINR(t.value)} />
        ))}
      </div>

      {["ceo","admin","sales_manager"].includes(user.role) && (
        <div className="flex flex-wrap gap-2 mb-4">
          <Select value={filters.salesperson_id || "all"} onValueChange={(v) => setFilters({...filters, salesperson_id: v === "all" ? "" : v})}>
            <SelectTrigger className="w-48" data-testid="pipeline-sp-filter"><SelectValue placeholder="Salesperson" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All salespeople</SelectItem>
              {salespersons.map((sp) => <SelectItem key={sp.id} value={sp.id}>{sp.name}</SelectItem>)}
            </SelectContent>
          </Select>
          <Input placeholder="Area" className="w-40" value={filters.area} onChange={(e) => setFilters({...filters, area: e.target.value})} />
        </div>
      )}

      {deals.length === 0 ? <EmptyState>Create your first deal to populate the pipeline.</EmptyState> : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
          <div className="flex gap-4 overflow-x-auto kanban-scroll pb-4 -mx-4 px-4">
            {STAGES.map((stage) => (
              <Column key={stage} stage={stage} deals={deals.filter((d) => d.stage === stage)} />
            ))}
          </div>
        </DndContext>
      )}
    </div>
  );
}

function Column({ stage, deals }) {
  const { setNodeRef, isOver } = useDroppable({ id: stage });
  const meta = stageMeta[stage];
  return (
    <div ref={setNodeRef} className={`flex-shrink-0 w-72 md:w-80 ${isOver ? "ring-2 ring-[hsl(var(--accent))]/50" : ""}`} data-testid={`column-${stage}`}>
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-border">
        <div className="flex items-center gap-2">
          <span className={`h-2.5 w-2.5 rounded-full ${meta.color}`}></span>
          <span className="overline">{meta.label}</span>
        </div>
        <span className="text-xs font-mono font-bold">{deals.length}</span>
      </div>
      <div className="space-y-2 min-h-[500px]">
        {deals.map((d) => <DealCard key={d.id} deal={d} />)}
      </div>
    </div>
  );
}

function DealCard({ deal }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id: deal.id });
  const style = transform ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`, opacity: isDragging ? 0.7 : 1 } : {};
  const followUpDays = daysUntil(deal.next_follow_up);
  const followUpColor =
    followUpDays == null ? "text-muted-foreground" :
    followUpDays < 0 ? "text-red-500" :
    followUpDays === 0 ? "text-amber-500" : "text-emerald-500";
  const meta = stageMeta[deal.stage];

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      data-testid={`deal-card-${deal.id}`}
      className="border border-border rounded-md bg-card p-3 cursor-grab active:cursor-grabbing hover:border-foreground/40 relative"
    >
      <div className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-md ${meta.color}`} />
      <div className="pl-1">
        <div className="flex justify-between items-start gap-2">
          <div className="font-heading font-bold text-sm leading-snug">{deal.client_name}</div>
          <ArrowsOutCardinal size={14} className="text-muted-foreground flex-shrink-0" />
        </div>
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground mt-0.5">{deal.client_type} · {deal.area}</div>

        <div className="mt-2.5 flex items-baseline justify-between">
          <div className="text-xs">
            <div className="text-muted-foreground">POC</div>
            <div className="font-semibold">{deal.poc_name || "—"}</div>
          </div>
          <div className="font-mono font-bold text-sm">{formatINR(deal.estimated_value)}</div>
        </div>

        <div className="mt-3 pt-2 border-t border-border/60 flex justify-between text-[10px]">
          <span className={`font-mono ${followUpColor}`}>
            ◷ {formatDate(deal.next_follow_up)}
          </span>
          <span className="text-muted-foreground font-mono">{deal.touchpoints || 0} ⋅ touches</span>
        </div>
      </div>
    </div>
  );
}

function DealForm({ onClose }) {
  const [form, setForm] = useState({
    client_name: "", client_type: "Fabricator", area: "",
    poc_name: "", poc_contact: "", estimated_value: 0, next_follow_up: "", notes: "",
    stage: "COLD_LEAD",
  });
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const payload = { ...form, estimated_value: Number(form.estimated_value), next_follow_up: form.next_follow_up || null };
      await api.post("/deals", payload);
      toast.success("Deal added");
      onClose();
    } catch { toast.error("Failed"); } finally { setBusy(false); }
  };
  return (
    <form onSubmit={submit} className="space-y-3 mt-4">
      <SheetHeader><SheetTitle className="font-heading">New deal</SheetTitle></SheetHeader>
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2"><Label>Client</Label><Input required value={form.client_name} onChange={(e) => setForm({...form, client_name: e.target.value})} data-testid="deal-client-input" /></div>
        <div>
          <Label>Type</Label>
          <Select value={form.client_type} onValueChange={(v) => setForm({...form, client_type: v})}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>{["Fabricator","Transporter","Dealer","PSU","Other"].map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
          </Select>
        </div>
        <div><Label>Area</Label><Input value={form.area} onChange={(e) => setForm({...form, area: e.target.value})} /></div>
        <div><Label>POC Name</Label><Input value={form.poc_name} onChange={(e) => setForm({...form, poc_name: e.target.value})} /></div>
        <div><Label>POC Contact</Label><Input value={form.poc_contact} onChange={(e) => setForm({...form, poc_contact: e.target.value})} /></div>
        <div><Label>Est. Value (₹)</Label><Input type="number" value={form.estimated_value} onChange={(e) => setForm({...form, estimated_value: e.target.value})} data-testid="deal-value-input" /></div>
        <div><Label>Next follow-up</Label><Input type="date" value={form.next_follow_up} onChange={(e) => setForm({...form, next_follow_up: e.target.value})} /></div>
        <div className="col-span-2"><Label>Notes</Label><Textarea rows={2} value={form.notes} onChange={(e) => setForm({...form, notes: e.target.value})} /></div>
      </div>
      <Button type="submit" disabled={busy} className="w-full" data-testid="deal-save-btn">{busy ? "Saving…" : "Save"}</Button>
    </form>
  );
}
