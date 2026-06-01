import React, { useEffect, useState } from "react";
import api from "../lib/api";
import { PageHeader, EmptyState } from "../components/Common";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "../components/ui/sheet";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Plus, Phone, WhatsappLogo, Envelope } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function POCs() {
  const [pocs, setPocs] = useState([]);
  const [open, setOpen] = useState(false);
  const [flwOpen, setFlwOpen] = useState(false);
  const [selectedPoc, setSelectedPoc] = useState(null);

  const load = async () => {
    const { data } = await api.get("/pocs");
    setPocs(data);
  };
  useEffect(() => { load(); }, []);

  return (
    <div>
      <PageHeader
        overline="Module 2"
        title="POC Database"
        subtitle="Decision-maker contacts captured during visits. Schedule follow-ups directly."
        actions={
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button data-testid="new-poc-btn"><Plus size={16} className="mr-1.5" weight="bold" /> Capture POC</Button>
            </SheetTrigger>
            <SheetContent className="overflow-y-auto w-full sm:max-w-lg">
              <POCForm onClose={() => { setOpen(false); load(); }} />
            </SheetContent>
          </Sheet>
        }
      />

      {pocs.length === 0 ? <EmptyState>Capture your first POC after a visit without immediate sale.</EmptyState> : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {pocs.map((p) => (
            <div key={p.id} className="border border-border rounded-md p-4 bg-card" data-testid={`poc-card-${p.id}`}>
              <div className="overline">{p.client_name}</div>
              <div className="font-heading font-bold mt-1 text-base">{p.poc_name}</div>
              <div className="text-xs text-muted-foreground">{p.designation}</div>
              <div className="mt-3 space-y-1.5 text-xs">
                <div className="flex items-center gap-2"><Phone size={12} /> <span className="font-mono">{p.mobile}</span></div>
                {p.whatsapp && <div className="flex items-center gap-2"><WhatsappLogo size={12} /> <span className="font-mono">{p.whatsapp}</span></div>}
                {p.email && <div className="flex items-center gap-2"><Envelope size={12} /> <span className="font-mono truncate">{p.email}</span></div>}
              </div>
              <div className="mt-3 pt-3 border-t border-border flex justify-between items-center">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Best: {p.best_time || "Any"}</div>
                <Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => { setSelectedPoc(p); setFlwOpen(true); }} data-testid={`schedule-followup-${p.id}`}>
                  + Follow-up
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Sheet open={flwOpen} onOpenChange={setFlwOpen}>
        <SheetContent className="w-full sm:max-w-lg">
          {selectedPoc && <FollowUpForm poc={selectedPoc} onClose={() => { setFlwOpen(false); }} />}
        </SheetContent>
      </Sheet>
    </div>
  );
}

function POCForm({ onClose }) {
  const [form, setForm] = useState({
    client_name: "", poc_name: "", designation: "", mobile: "", email: "",
    whatsapp: "", best_time: "", preferred_method: "Call", notes: "", area: "", client_type: "Fabricator",
  });
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/pocs", form);
      toast.success("POC saved");
      onClose();
    } catch { toast.error("Failed"); } finally { setBusy(false); }
  };

  return (
    <form onSubmit={submit} className="space-y-3 mt-4">
      <SheetHeader><SheetTitle className="font-heading">Capture POC</SheetTitle></SheetHeader>
      <div className="grid grid-cols-2 gap-3">
        <div><Label>Client</Label><Input required value={form.client_name} onChange={(e) => setForm({...form, client_name: e.target.value})} data-testid="poc-client-input" /></div>
        <div><Label>POC Name</Label><Input required value={form.poc_name} onChange={(e) => setForm({...form, poc_name: e.target.value})} data-testid="poc-name-input" /></div>
        <div><Label>Designation</Label><Input value={form.designation} onChange={(e) => setForm({...form, designation: e.target.value})} /></div>
        <div><Label>Area</Label><Input value={form.area} onChange={(e) => setForm({...form, area: e.target.value})} /></div>
        <div><Label>Mobile</Label><Input required value={form.mobile} onChange={(e) => setForm({...form, mobile: e.target.value})} data-testid="poc-mobile-input" /></div>
        <div><Label>WhatsApp</Label><Input value={form.whatsapp} onChange={(e) => setForm({...form, whatsapp: e.target.value})} /></div>
        <div className="col-span-2"><Label>Email</Label><Input type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} /></div>
        <div><Label>Best time</Label><Input placeholder="e.g. 10am–12pm" value={form.best_time} onChange={(e) => setForm({...form, best_time: e.target.value})} /></div>
        <div>
          <Label>Preferred</Label>
          <Select value={form.preferred_method} onValueChange={(v) => setForm({...form, preferred_method: v})}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="Call">Call</SelectItem>
              <SelectItem value="WhatsApp">WhatsApp</SelectItem>
              <SelectItem value="Email">Email</SelectItem>
              <SelectItem value="Visit">Visit</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="col-span-2"><Label>Notes</Label><Textarea rows={2} value={form.notes} onChange={(e) => setForm({...form, notes: e.target.value})} /></div>
      </div>
      <Button type="submit" disabled={busy} className="w-full" data-testid="poc-save-btn">{busy ? "Saving…" : "Save POC"}</Button>
    </form>
  );
}

function FollowUpForm({ poc, onClose }) {
  const [date, setDate] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/followups", { poc_id: poc.id, due_date: date, notes });
      toast.success("Follow-up scheduled");
      onClose();
    } catch { toast.error("Failed"); } finally { setBusy(false); }
  };
  return (
    <form onSubmit={submit} className="space-y-4 mt-4">
      <SheetHeader><SheetTitle className="font-heading">Schedule follow-up</SheetTitle></SheetHeader>
      <div className="text-sm">For <span className="font-bold">{poc.poc_name}</span> at <span className="font-bold">{poc.client_name}</span></div>
      <div><Label>Due date</Label><Input type="date" required value={date} onChange={(e) => setDate(e.target.value)} data-testid="followup-date-input" /></div>
      <div><Label>Notes</Label><Textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} /></div>
      <Button type="submit" disabled={busy} className="w-full" data-testid="followup-save-btn">{busy ? "Saving…" : "Schedule"}</Button>
    </form>
  );
}
