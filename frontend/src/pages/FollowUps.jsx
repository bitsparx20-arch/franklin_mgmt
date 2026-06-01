import React, { useEffect, useState } from "react";
import api from "../lib/api";
import { PageHeader, EmptyState, StatCard } from "../components/Common";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "../components/ui/sheet";
import { useAuth } from "../context/AuthContext";
import { Bell, Warning, Check } from "@phosphor-icons/react";
import { toast } from "sonner";
import { formatDate } from "../lib/format";

const ACTIONS = ["Called", "Visited", "Email Sent", "WhatsApp Sent", "No Response"];

export default function FollowUps() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [current, setCurrent] = useState(null);
  const [action, setAction] = useState("Called");
  const [notes, setNotes] = useState("");

  const load = async () => {
    const { data } = await api.get("/followups");
    setItems(data);
  };
  useEffect(() => { load(); }, []);

  const due_today = items.filter((f) => f.status === "pending" && (f.due_date || "").slice(0, 10) === new Date().toISOString().slice(0, 10)).length;
  const overdue = items.filter((f) => f.is_overdue).length;
  const completed = items.filter((f) => f.status === "completed").length;

  const escalate = async () => {
    try {
      const { data } = await api.post("/followups/escalate-overdue");
      toast.success(`Escalated ${data.escalated} overdue items`);
      load();
    } catch { toast.error("Need manager+ role"); }
  };

  const submitLog = async (e) => {
    e.preventDefault();
    try {
      const { data } = await api.post(`/followups/${current.id}/log`, { action, notes });
      toast.success(`Logged: ${action}`);
      if (action === "WhatsApp Sent" && data?.messaging) {
        const st = data.messaging.status;
        if (st === "mocked") toast.message("WhatsApp logged (add SPRINGEDGE_API_KEY to send live)");
        else if (st === "failed" || st === "skipped") toast.error(data.messaging.error || data.messaging.reason || "Message not sent");
        else toast.success("Sent via SpringEdge");
      }
      setOpen(false); setNotes("");
      load();
    } catch { toast.error("Failed"); }
  };

  return (
    <div>
      <PageHeader
        overline="Module 2 · Module 8"
        title="Follow-ups & Reminders"
        subtitle="Daily reminders for due POCs. Overdue items auto-escalate to your manager."
        actions={["ceo","admin","sales_manager"].includes(user.role) && (
          <Button variant="outline" onClick={escalate} data-testid="escalate-btn"><Warning size={16} className="mr-1.5" weight="bold" /> Escalate overdue</Button>
        )}
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard label="Total" value={items.length} />
        <StatCard label="Due today" value={due_today} accent="text-amber-600" />
        <StatCard label="Overdue" value={overdue} accent="text-red-600" />
        <StatCard label="Completed" value={completed} accent="text-emerald-600" />
      </div>

      {items.length === 0 ? <EmptyState>Schedule a follow-up from the POCs page.</EmptyState> : (
        <div className="space-y-2">
          {items.map((f) => (
            <div key={f.id} className={`border rounded-md p-4 bg-card flex flex-col md:flex-row md:items-center gap-3 ${
              f.is_overdue ? "border-red-500/40" : f.status === "completed" ? "border-emerald-500/30" : "border-border"
            }`} data-testid={`followup-row-${f.id}`}>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Bell size={14} className={f.is_overdue ? "text-red-500" : "text-muted-foreground"} weight={f.is_overdue ? "fill" : "regular"} />
                  <span className="font-heading font-bold">{f.poc_name}</span>
                  <span className="text-xs text-muted-foreground">@ {f.client_name}</span>
                </div>
                {f.notes && <div className="text-xs text-muted-foreground">{f.notes}</div>}
                {f.logs?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {f.logs.slice(-3).map((l, i) => (
                      <Badge key={i} variant="secondary" className="text-[10px]">{l.action}</Badge>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-3 text-xs">
                <div>
                  <div className="overline">Due</div>
                  <div className={`font-mono font-bold ${f.is_overdue ? "text-red-500" : ""}`}>{formatDate(f.due_date)}</div>
                </div>
                <div>
                  <div className="overline">Status</div>
                  <Badge className={f.status === "completed" ? "bg-emerald-600" : f.is_overdue ? "bg-red-600" : "bg-amber-500"}>{f.status}</Badge>
                </div>
                {f.status !== "completed" && (
                  <Button size="sm" onClick={() => { setCurrent(f); setOpen(true); }} data-testid={`log-action-${f.id}`}>Log action</Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent className="w-full sm:max-w-md">
          <form onSubmit={submitLog} className="space-y-4 mt-4">
            <SheetHeader><SheetTitle className="font-heading">Log follow-up action</SheetTitle></SheetHeader>
            {current && <div className="text-sm">{current.poc_name} @ {current.client_name}</div>}
            <div>
              <label className="text-xs uppercase tracking-wider">Action</label>
              <Select value={action} onValueChange={setAction}>
                <SelectTrigger data-testid="action-select"><SelectValue /></SelectTrigger>
                <SelectContent>{ACTIONS.map((a) => <SelectItem key={a} value={a}>{a}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs uppercase tracking-wider">Notes</label>
              <Textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
            </div>
            <Button type="submit" className="w-full" data-testid="log-save-btn"><Check size={16} className="mr-1.5" weight="bold" /> Save log</Button>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}
