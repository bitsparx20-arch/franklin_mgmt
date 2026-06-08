import React, { useEffect, useState } from "react";
import api from "../lib/api";
import { PageHeader, StatCard, EmptyState } from "../components/Common";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "../components/ui/sheet";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Plus, MapPin, Crosshair } from "@phosphor-icons/react";
import { toast } from "sonner";
import { formatDateTime } from "../lib/format";

const CLIENT_TYPES = ["Fabricator", "Transporter", "Dealer", "PSU", "Other"];
const STATUSES = ["Completed", "Follow-up", "Converted"];

export default function Visits() {
  const [visits, setVisits] = useState([]);
  const [open, setOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState("");
  const [filterType, setFilterType] = useState("");

  const load = async () => {
    const params = {};
    if (filterStatus) params.status = filterStatus;
    if (filterType) params.client_type = filterType;
    const { data } = await api.get("/visits", { params });
    setVisits(data);
  };

  useEffect(() => { load(); }, [filterStatus, filterType]);

  return (
    <div>
      <PageHeader
        overline="Module 1"
        title="Visit Tracking"
        subtitle="Log every field visit. GPS auto-captured. Linked to your sales record."
        actions={
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button data-testid="new-visit-btn" className="rounded-md"><Plus size={16} className="mr-1.5" weight="bold" /> New Visit</Button>
            </SheetTrigger>
            <SheetContent className="overflow-y-auto w-full sm:max-w-lg">
              <VisitForm onClose={() => { setOpen(false); load(); }} />
            </SheetContent>
          </Sheet>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard label="Total visits" value={visits.length} />
        <StatCard label="Completed" value={visits.filter(v => v.status === "Completed").length} />
        <StatCard label="Follow-ups" value={visits.filter(v => v.status === "Follow-up").length} accent="text-amber-600" />
        <StatCard label="Converted" value={visits.filter(v => v.status === "Converted").length} accent="text-emerald-600" />
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        <Select value={filterStatus || "all"} onValueChange={(v) => setFilterStatus(v === "all" ? "" : v)}>
          <SelectTrigger className="w-40" data-testid="visits-status-filter"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All status</SelectItem>
            {STATUSES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={filterType || "all"} onValueChange={(v) => setFilterType(v === "all" ? "" : v)}>
          <SelectTrigger className="w-44" data-testid="visits-type-filter"><SelectValue placeholder="Client type" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            {CLIENT_TYPES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {visits.length === 0 ? <EmptyState>Log your first visit to populate the dashboard.</EmptyState> : (
        <>
        {/* Mobile cards */}
        <div className="md:hidden space-y-2">
          {visits.map((v) => (
            <div key={v.id} className="border border-border rounded-md p-3 bg-card" data-testid={`visit-card-${v.id}`}>
              <div className="flex justify-between items-start gap-2">
                <div className="font-heading font-bold text-sm">{v.client_name}</div>
                <Badge className={
                  v.status === "Converted" ? "bg-emerald-600" :
                  v.status === "Follow-up" ? "bg-amber-500" : "bg-zinc-500"
                }>{v.status}</Badge>
              </div>
              <div className="mt-1 flex items-center gap-2 text-[10px] uppercase tracking-wider text-muted-foreground">
                <Badge variant="secondary" className="text-[10px]">{v.client_type}</Badge>
                <span>{formatDateTime(v.visit_date)}</span>
              </div>
              <div className="mt-1.5 text-xs">{v.location_text}</div>
              {v.lat && <div className="font-mono text-muted-foreground text-[10px]">{v.lat.toFixed(3)}, {v.lng.toFixed(3)}</div>}
            </div>
          ))}
        </div>
        {/* Desktop table */}
        <div className="hidden md:block border border-border rounded-md overflow-x-auto bg-card">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left">
              <tr className="border-b border-border">
                <th className="px-4 py-2.5 font-heading font-bold text-xs uppercase tracking-wider">Client</th>
                <th className="px-4 py-2.5 font-heading font-bold text-xs uppercase tracking-wider">Type</th>
                <th className="px-4 py-2.5 font-heading font-bold text-xs uppercase tracking-wider">Location</th>
                <th className="px-4 py-2.5 font-heading font-bold text-xs uppercase tracking-wider">Date</th>
                <th className="px-4 py-2.5 font-heading font-bold text-xs uppercase tracking-wider">Salesperson</th>
                <th className="px-4 py-2.5 font-heading font-bold text-xs uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody>
              {visits.map((v) => (
                <tr key={v.id} className="border-b border-border/50 hover:bg-muted/30" data-testid={`visit-row-desktop-${v.id}`}>
                  <td className="px-4 py-3 font-semibold">{v.client_name}</td>
                  <td className="px-4 py-3"><Badge variant="secondary">{v.client_type}</Badge></td>
                  <td className="px-4 py-3 text-xs">
                    <div>{v.location_text}</div>
                    {v.lat && <div className="font-mono text-muted-foreground text-[10px]">{v.lat.toFixed(3)}, {v.lng.toFixed(3)}</div>}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{formatDateTime(v.visit_date)}</td>
                  <td className="px-4 py-3 text-xs">{v.salesperson_name}</td>
                  <td className="px-4 py-3">
                    <Badge className={
                      v.status === "Converted" ? "bg-emerald-600" :
                      v.status === "Follow-up" ? "bg-amber-500" : "bg-zinc-500"
                    }>{v.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        </>
      )}
    </div>
  );
}

function VisitForm({ onClose }) {
  const [form, setForm] = useState({
    client_name: "", client_type: "Fabricator", custom_client_type: "",
    location_text: "", lat: null, lng: null, remarks: "", status: "Completed",
  });
  const [busy, setBusy] = useState(false);
  const isOtherType = form.client_type === "Other";

  const captureGPS = () => {
    if (!navigator.geolocation) return toast.error("Geolocation not supported");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm((f) => ({ ...f, lat: pos.coords.latitude, lng: pos.coords.longitude }));
        toast.success("GPS captured");
      },
      () => toast.error("Permission denied or unavailable")
    );
  };

  const submit = async (e) => {
    e.preventDefault();
    if (isOtherType && !form.custom_client_type.trim()) {
      return toast.error("Enter a custom client type");
    }
    setBusy(true);
    try {
      const { custom_client_type, ...rest } = form;
      const payload = {
        ...rest,
        client_type: isOtherType ? custom_client_type.trim() : form.client_type,
      };
      await api.post("/visits", payload);
      toast.success("Visit logged");
      onClose();
    } catch (err) {
      toast.error("Failed to save");
    } finally { setBusy(false); }
  };

  return (
    <form onSubmit={submit} className="space-y-4 mt-4">
      <SheetHeader>
        <SheetTitle className="font-heading">Log new visit</SheetTitle>
      </SheetHeader>
      <div>
        <Label>Client name</Label>
        <Input required value={form.client_name} onChange={(e) => setForm({...form, client_name: e.target.value})} data-testid="visit-client-input" />
      </div>
      <div>
        <Label>Client type</Label>
        <Select
          value={form.client_type}
          onValueChange={(v) => setForm({ ...form, client_type: v, custom_client_type: v === "Other" ? form.custom_client_type : "" })}
        >
          <SelectTrigger data-testid="visit-type-select"><SelectValue /></SelectTrigger>
          <SelectContent>{CLIENT_TYPES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent>
        </Select>
        {isOtherType && (
          <Input
            className="mt-2"
            required
            placeholder="Type custom client type…"
            value={form.custom_client_type}
            onChange={(e) => setForm({ ...form, custom_client_type: e.target.value })}
            data-testid="visit-custom-type-input"
          />
        )}
      </div>
      <div>
        <Label>Location</Label>
        <div className="flex gap-2">
          <Input required value={form.location_text} onChange={(e) => setForm({...form, location_text: e.target.value})} placeholder="Area / address" data-testid="visit-location-input" />
          <Button type="button" variant="outline" onClick={captureGPS} data-testid="capture-gps-btn"><Crosshair size={16} /></Button>
        </div>
        {form.lat && <div className="text-[10px] font-mono text-muted-foreground mt-1">GPS: {form.lat.toFixed(4)}, {form.lng.toFixed(4)}</div>}
      </div>
      <div>
        <Label>Remarks</Label>
        <Textarea value={form.remarks} onChange={(e) => setForm({...form, remarks: e.target.value})} rows={3} />
      </div>
      <div>
        <Label>Status</Label>
        <Select value={form.status} onValueChange={(v) => setForm({...form, status: v})}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>{STATUSES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
        </Select>
      </div>
      <Button type="submit" disabled={busy} className="w-full" data-testid="visit-save-btn">{busy ? "Saving…" : "Save visit"}</Button>
    </form>
  );
}
