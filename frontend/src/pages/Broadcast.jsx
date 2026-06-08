import React, { useEffect, useMemo, useState } from "react";
import api from "../lib/api";
import { PageHeader, EmptyState, StatCard } from "../components/Common";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Checkbox } from "../components/ui/checkbox";
import {
  Megaphone, ChatCircle, WhatsappLogo, PaperPlaneTilt,
  CheckCircle, XCircle, ClockCounterClockwise, Plugs,
} from "@phosphor-icons/react";
import { toast } from "sonner";
import { formatDate } from "../lib/format";

const CHANNELS = [
  { id: "sms", label: "SMS", icon: ChatCircle },
  { id: "whatsapp", label: "WhatsApp", icon: WhatsappLogo },
];

const DEFAULT_WA_TEMPLATE = "lms_notification";

function lmsNotificationPreview(alert, msg) {
  const a = (alert || "Pipeline update").trim();
  const m = (msg || "Your message…").trim();
  return (
    <div className="rounded-lg bg-[#e7f8ee] dark:bg-emerald-950/30 p-3 text-[13px] leading-relaxed text-foreground shadow-inner border border-emerald-200/60 dark:border-emerald-800/40">
      <div className="font-bold text-sm mb-2">lms notification</div>
      <div>Notification Alert: {a || "{{1}}"}</div>
      <div className="mt-1">Msg: {m || "{{2}}"}</div>
      <div className="mt-2 text-muted-foreground text-xs">Thanks, LMS Tech Team</div>
    </div>
  );
}

export default function Broadcast() {
  const [status, setStatus] = useState(null);
  const [recipients, setRecipients] = useState([]);
  const [logs, setLogs] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [channel, setChannel] = useState("sms");
  const [alertTitle, setAlertTitle] = useState("Pipeline update");
  const [message, setMessage] = useState("");
  const [manualPhone, setManualPhone] = useState("");
  const [manualPhones, setManualPhones] = useState([]);
  const [templateName, setTemplateName] = useState(DEFAULT_WA_TEMPLATE);
  const [areaFilter, setAreaFilter] = useState("all");
  const [busy, setBusy] = useState(false);
  const [search, setSearch] = useState("");

  const load = async () => {
    const [st, rec, lg] = await Promise.all([
      api.get("/messaging/status"),
      api.get("/messaging/recipients"),
      api.get("/messaging/logs"),
    ]);
    setStatus(st.data);
    setRecipients(rec.data);
    setLogs(lg.data);
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (status?.whatsapp_template) {
      setTemplateName(status.whatsapp_template);
    }
  }, [status?.whatsapp_template]);

  const waTemplate = templateName || status?.whatsapp_template || DEFAULT_WA_TEMPLATE;

  const areas = useMemo(() => {
    const set = new Set(recipients.map((r) => r.area).filter(Boolean));
    return ["all", ...Array.from(set).sort()];
  }, [recipients]);

  const filtered = useMemo(() => {
    let list = recipients;
    if (areaFilter !== "all") list = list.filter((r) => r.area === areaFilter);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (r) =>
          r.client_name?.toLowerCase().includes(q) ||
          r.poc_name?.toLowerCase().includes(q) ||
          r.phone?.includes(q)
      );
    }
    return list;
  }, [recipients, areaFilter, search]);

  const toggle = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAllFiltered = () => {
    setSelected(new Set(filtered.map((r) => r.id)));
  };

  const clearSelection = () => setSelected(new Set());

  const addManual = () => {
    const p = manualPhone.trim();
    if (!p) return;
    if (manualPhones.includes(p)) return toast.message("Number already added");
    setManualPhones((m) => [...m, p]);
    setManualPhone("");
  };

  const send = async () => {
    if (!message.trim()) return toast.error("Enter a message");
    if (channel === "whatsapp" && !alertTitle.trim()) return toast.error("Enter an alert title for {{1}}");
    if (selected.size === 0 && manualPhones.length === 0) {
      return toast.error("Select recipients or add phone numbers");
    }
    setBusy(true);
    try {
      const body = {
        message: message.trim(),
        channel,
        poc_ids: Array.from(selected),
        phones: manualPhones,
      };
      if (channel === "whatsapp") {
        body.template_name = waTemplate;
        body.alert_title = alertTitle.trim();
        body.template_params = [alertTitle.trim(), message.trim()];
      }
      const { data } = await api.post("/messaging/broadcast", body);
      if (data.mocked > 0 && data.sent === 0) {
        toast.message(`MOCKED — ${data.mocked} message(s) logged (add SpringEdge keys to send live)`);
      } else if (data.failed > 0) {
        toast.error(`Sent ${data.sent}, failed ${data.failed}`);
      } else {
        const smsFallback = data.results?.some(
          (r) => r.detail?.delivery_mode === "whatsapp_sms_fallback"
        );
        toast.success(
          smsFallback
            ? `Broadcast sent — delivered via SMS fallback (WhatsApp unavailable)`
            : `Broadcast sent to ${data.total} recipient(s)`
        );
      }
      setMessage("");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Broadcast failed");
    } finally {
      setBusy(false);
    }
  };

  const sentToday = logs.filter((l) => (l.sent_at || "").slice(0, 10) === new Date().toISOString().slice(0, 10)).length;
  const failedRecent = logs.filter((l) => l.status === "failed").length;

  return (
    <div data-testid="broadcast-page">
      <PageHeader
        overline="Outreach"
        title="Broadcast"
        actions={
          <Badge variant="outline" className="gap-1.5 py-1.5 px-2.5 font-normal">
            <Plugs size={14} />
            {status?.whatsapp_configured
              ? "WhatsApp + SMS fallback"
              : status?.sms_configured
                ? status?.demo_sms_mode
                  ? "Trial SMS (mandatory WA fallback)"
                  : "SMS live (mandatory WA fallback)"
                : "Mock mode"}
          </Badge>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard label="POC contacts" value={recipients.length} sub="With phone / WhatsApp" />
        <StatCard label="Selected" value={selected.size + manualPhones.length} accent="text-[hsl(var(--accent))]" />
        <StatCard label="Sent today" value={sentToday} />
        <StatCard label="Recent failures" value={failedRecent} accent={failedRecent ? "text-red-600" : ""} />
      </div>

      <Tabs defaultValue="compose" className="space-y-4">
        <TabsList>
          <TabsTrigger value="compose" data-testid="broadcast-tab-compose">
            <Megaphone size={16} className="mr-1.5" /> Compose
          </TabsTrigger>
          <TabsTrigger value="history" data-testid="broadcast-tab-history">
            <ClockCounterClockwise size={16} className="mr-1.5" /> History
          </TabsTrigger>
        </TabsList>

        <TabsContent value="compose">
          <div className="grid lg:grid-cols-5 gap-4 md:gap-6">
            {/* Compose panel */}
            <div className="lg:col-span-2 space-y-4">
            <div className="border border-border rounded-md p-4 md:p-5 bg-card space-y-4">
              <div>
                <Label className="text-xs uppercase tracking-wider">Channel</Label>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {CHANNELS.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      data-testid={`broadcast-channel-${c.id}`}
                      onClick={() => setChannel(c.id)}
                      className={`rounded-md border p-3 text-left transition-colors ${
                        channel === c.id
                          ? "border-foreground bg-muted"
                          : "border-border hover:bg-muted/50"
                      }`}
                    >
                      <c.icon size={20} weight={channel === c.id ? "fill" : "regular"} className="mb-1" />
                      <div className="text-sm font-semibold">{c.label}</div>
                    </button>
                  ))}
                </div>
              </div>

              {channel === "whatsapp" ? (
                <div className="space-y-3">
                  <div>
                    <Label className="text-xs uppercase tracking-wider">Notification alert</Label>
                    <Input
                      className="mt-1.5"
                      placeholder="e.g. Pipeline update"
                      value={alertTitle}
                      onChange={(e) => setAlertTitle(e.target.value)}
                      data-testid="broadcast-alert-title"
                    />
                  </div>
                  <div>
                    <Label className="text-xs uppercase tracking-wider">Message</Label>
                    <Textarea
                      className="mt-1.5 min-h-[100px] font-sans"
                      placeholder="Your message to the recipient…"
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      data-testid="broadcast-message-input"
                    />
                  </div>
                  <div>
                    <Label className="text-xs uppercase tracking-wider">Preview</Label>
                    <div className="mt-1.5" data-testid="broadcast-wa-preview">
                      {lmsNotificationPreview(alertTitle, message)}
                    </div>
                  </div>
                </div>
              ) : (
                <div>
                  <Label className="text-xs uppercase tracking-wider">Message</Label>
                  <Textarea
                    className="mt-2 min-h-[140px] font-sans"
                    placeholder="Your SMS message to selected POCs…"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    data-testid="broadcast-message-input"
                  />
                  <div className="text-[10px] text-muted-foreground mt-1 font-mono">{message.length} chars</div>
                </div>
              )}

              <div>
                <Label className="text-xs uppercase tracking-wider">Manual numbers</Label>
                <div className="flex gap-2 mt-2">
                  <Input
                    placeholder="+91XXXXXXXXXX"
                    value={manualPhone}
                    onChange={(e) => setManualPhone(e.target.value)}
                    data-testid="broadcast-manual-phone"
                    className="font-mono"
                  />
                  <Button type="button" variant="outline" onClick={addManual}>Add</Button>
                </div>
                {manualPhones.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {manualPhones.map((p) => (
                      <Badge key={p} variant="secondary" className="font-mono text-[10px] gap-1">
                        {p}
                        <button type="button" onClick={() => setManualPhones((m) => m.filter((x) => x !== p))} className="opacity-60 hover:opacity-100">×</button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <Button
                className="w-full"
                disabled={busy}
                onClick={send}
                data-testid="broadcast-send-btn"
              >
                <PaperPlaneTilt size={16} weight="bold" className="mr-1.5" />
                {busy ? "Sending…" : `Send ${channel === "whatsapp" ? "WhatsApp" : "SMS"} broadcast`}
              </Button>

              {!status?.configured && (
                <p className="text-xs text-amber-700 dark:text-amber-400 border border-amber-500/30 rounded-md p-2.5 bg-amber-500/5">
                  Mock mode — set SpringEdge keys in backend/.env to send live.
                </p>
              )}
            </div>
            </div>

            {/* Recipients */}
            <div className="lg:col-span-3 border border-border rounded-md bg-card overflow-hidden flex flex-col max-h-[720px]">
              <div className="p-4 border-b border-border flex flex-col sm:flex-row sm:items-center gap-2 justify-between">
                <div>
                  <div className="font-heading font-bold">Recipients</div>
                  <div className="text-xs text-muted-foreground">POC contacts from your scope</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" variant="outline" onClick={selectAllFiltered}>Select all</Button>
                  <Button size="sm" variant="ghost" onClick={clearSelection}>Clear</Button>
                </div>
              </div>
              <div className="p-3 border-b border-border flex flex-col sm:flex-row gap-2">
                <Input
                  placeholder="Search client, POC, phone…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  data-testid="broadcast-recipient-search"
                  className="sm:flex-1"
                />
                <select
                  className="h-10 rounded-md border border-border bg-background px-3 text-sm"
                  value={areaFilter}
                  onChange={(e) => setAreaFilter(e.target.value)}
                  data-testid="broadcast-area-filter"
                >
                  {areas.map((a) => (
                    <option key={a} value={a}>{a === "all" ? "All areas" : a}</option>
                  ))}
                </select>
              </div>
              <div className="flex-1 overflow-y-auto divide-y divide-border/60">
                {filtered.length === 0 ? (
                  <div className="p-8 text-center text-sm text-muted-foreground">
                    {recipients.length === 0 ? "No POC contacts with phone numbers yet." : "No matches."}
                  </div>
                ) : (
                  filtered.map((r) => (
                    <label
                      key={r.id}
                      className="flex items-start gap-3 p-3 hover:bg-muted/40 cursor-pointer"
                      data-testid={`broadcast-recipient-${r.id}`}
                    >
                      <Checkbox
                        checked={selected.has(r.id)}
                        onCheckedChange={() => toggle(r.id)}
                        className="mt-0.5"
                      />
                      <div className="min-w-0 flex-1">
                        <div className="font-semibold text-sm truncate">{r.poc_name}</div>
                        <div className="text-xs text-muted-foreground truncate">{r.client_name}</div>
                        <div className="text-[10px] font-mono text-muted-foreground mt-0.5">{r.phone}</div>
                      </div>
                      <div className="text-[10px] text-muted-foreground shrink-0 text-right max-w-[100px] truncate">{r.area}</div>
                    </label>
                  ))
                )}
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="history">
          {logs.length === 0 ? (
            <EmptyState>No messages sent yet. Compose a broadcast to get started.</EmptyState>
          ) : (
            <div className="border border-border rounded-md overflow-hidden bg-card">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/40 text-left">
                      <th className="p-3 text-[10px] uppercase tracking-wider font-semibold">When</th>
                      <th className="p-3 text-[10px] uppercase tracking-wider font-semibold">Channel</th>
                      <th className="p-3 text-[10px] uppercase tracking-wider font-semibold">To</th>
                      <th className="p-3 text-[10px] uppercase tracking-wider font-semibold">Message</th>
                      <th className="p-3 text-[10px] uppercase tracking-wider font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((l) => (
                      <tr key={l.id} className="border-b border-border/50 hover:bg-muted/20" data-testid={`broadcast-log-${l.id}`}>
                        <td className="p-3 font-mono text-[11px] whitespace-nowrap">{formatDate(l.sent_at)}</td>
                        <td className="p-3">
                          <Badge variant="outline" className="text-[10px] uppercase">{l.channel}</Badge>
                        </td>
                        <td className="p-3">
                          <div className="font-mono text-xs">{l.to}</div>
                          {l.recipient_label && <div className="text-[10px] text-muted-foreground truncate max-w-[140px]">{l.recipient_label}</div>}
                        </td>
                        <td className="p-3 text-xs max-w-[240px] truncate">{l.message}</td>
                        <td className="p-3">
                          <StatusBadge status={l.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

const StatusBadge = ({ status }) => {
  if (status === "sent" || status === "queued") {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] uppercase font-semibold text-emerald-600">
        <CheckCircle size={12} weight="fill" /> {status}
      </span>
    );
  }
  if (status === "mocked") {
    return <Badge variant="secondary" className="text-[10px]">mocked</Badge>;
  }
  if (status === "failed") {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] uppercase font-semibold text-red-600">
        <XCircle size={12} weight="fill" /> failed
      </span>
    );
  }
  return <Badge variant="outline" className="text-[10px]">{status}</Badge>;
};
