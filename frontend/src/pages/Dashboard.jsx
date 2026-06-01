import React, { useEffect, useMemo, useState } from "react";
import api from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { PageHeader, StatCard } from "../components/Common";
import { Button } from "../components/ui/button";
import { formatINR, conversionColor, stageMeta } from "../lib/format";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, LineChart, Line, CartesianGrid,
  PieChart, Pie, Cell,
} from "recharts";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { Trophy, TrendUp, Users, Receipt as ReceiptIcon, ChartLineUp, MapTrifold, Crosshair } from "@phosphor-icons/react";
import { toast } from "sonner";

// Fix default leaflet icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Colored DivIcons per agent status
const agentIcon = (source, role) => {
  const color = source === "visit" ? "#10b981" : source === "ping" ? "#3b82f6" : "#a1a1aa";
  const ring = role === "sales_manager" ? "#ff5400" : "transparent";
  return L.divIcon({
    className: "",
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    html: `<div style="width:24px;height:24px;border-radius:50%;background:${color};border:3px solid ${ring === 'transparent' ? '#ffffff' : ring};box-shadow:0 2px 6px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:bold;font-family:JetBrains Mono">${role === 'sales_manager' ? 'M' : '·'}</div>`,
  });
};

function FitBounds({ points }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 0) return;
    const bounds = L.latLngBounds(points.map((p) => [p.lat, p.lng]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 7 });
  }, [points, map]);
  return null;
}

export default function Dashboard() {
  const { user } = useAuth();
  const [overview, setOverview] = useState(null);
  const [perf, setPerf] = useState([]);
  const [funnel, setFunnel] = useState(null);
  const [agents, setAgents] = useState([]);
  const [topProducts, setTopProducts] = useState([]);

  const load = async () => {
    const [o, p, f, t] = await Promise.all([
      api.get("/dashboard/overview"),
      api.get("/dashboard/performance"),
      api.get("/dashboard/funnel"),
      api.get("/dashboard/top-products"),
    ]);
    setOverview(o.data); setPerf(p.data); setFunnel(f.data); setTopProducts(t.data);
    if (["ceo", "admin", "sales_manager"].includes(user.role)) {
      try {
        const a = await api.get("/dashboard/agent-locations");
        setAgents(a.data);
      } catch {}
    }
  };

  useEffect(() => { load(); }, []);

  const stageBars = useMemo(() => {
    if (!overview) return [];
    const order = ["COLD_LEAD","CONTACTED","INTERESTED","NEGOTIATION","WON","LOST"];
    return order.map((s) => ({
      stage: stageMeta[s].label,
      value: overview.stages_summary[s]?.value || 0,
      count: overview.stages_summary[s]?.count || 0,
    }));
  }, [overview]);

  const COLORS = ["#a1a1aa","#3b82f6","#f59e0b","#ff5400","#10b981","#dc2626"];

  return (
    <div data-testid="dashboard-page">
      <PageHeader
        overline={user.role === "salesperson" ? "Your snapshot" : "Live control room"}
        title="Dashboard"
        subtitle="Funnel · Pipeline · Revenue · Field signals — real-time."
      />

      {/* KPI Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-8">
        <StatCard label="Visits" value={overview?.totals.visits ?? "—"} sub="Field logs" />
        <StatCard label="POCs Captured" value={overview?.totals.pocs ?? "—"} />
        <StatCard label="Pipeline Value" value={formatINR(overview?.totals.pipeline_value)} accent="text-[hsl(var(--accent))]" />
        <StatCard label="Billed Revenue" value={formatINR(overview?.totals.revenue)} accent="text-emerald-600 dark:text-emerald-400" />
      </div>

      <div className="grid lg:grid-cols-3 gap-4 md:gap-6 mb-8">
        {/* Pipeline by stage */}
        <div className="lg:col-span-2 border border-border rounded-md p-4 md:p-6 bg-card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="overline">Kanban pipeline value</div>
              <h3 className="font-heading font-bold text-xl mt-1">By stage</h3>
            </div>
            <ChartLineUp size={20} className="text-muted-foreground" />
          </div>
          <div style={{ height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={stageBars} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                <XAxis dataKey="stage" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" tickFormatter={(v) => v >= 100000 ? `${(v/100000).toFixed(1)}L` : v} />
                <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", fontSize: 12 }} formatter={(v) => formatINR(v)} />
                <Bar dataKey="value" radius={[4,4,0,0]}>
                  {stageBars.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Funnel */}
        <div className="border border-border rounded-md p-4 md:p-6 bg-card">
          <div className="overline mb-1">Conversion funnel</div>
          <h3 className="font-heading font-bold text-xl">Visit → Won</h3>
          <div className="mt-4 space-y-2">
            {funnel?.stages.map((s, i) => {
              const max = funnel.stages[0].value || 1;
              const pct = (s.value / max) * 100;
              return (
                <div key={s.label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold">{s.label}</span>
                    <span className="font-mono">{s.value}</span>
                  </div>
                  <div className="h-7 rounded bg-muted overflow-hidden">
                    <div className="h-full" style={{ width: `${Math.max(pct, 5)}%`, background: COLORS[i] }} />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="mt-4 pt-4 border-t border-border">
            <div className="overline">Billed Value</div>
            <div className="font-mono font-bold text-2xl mt-1 text-emerald-600 dark:text-emerald-400">{formatINR(funnel?.billed_value)}</div>
          </div>
        </div>
      </div>

      {/* Monthly trend */}
      <div className="grid lg:grid-cols-3 gap-4 md:gap-6 mb-8">
        <div className="lg:col-span-2 border border-border rounded-md p-4 md:p-6 bg-card">
          <div className="overline">Month-over-month revenue</div>
          <h3 className="font-heading font-bold text-xl mt-1">12-month trend</h3>
          <div style={{ height: 240 }} className="mt-4">
            <ResponsiveContainer>
              <LineChart data={overview?.monthly_revenue || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" tickFormatter={(v) => v >= 100000 ? `${(v/100000).toFixed(1)}L` : v} />
                <Tooltip formatter={(v) => formatINR(v)} contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", fontSize: 12 }} />
                <Line type="monotone" dataKey="revenue" stroke="hsl(var(--accent))" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top products */}
        <div className="border border-border rounded-md p-4 md:p-6 bg-card">
          <div className="overline">Top-selling products</div>
          <h3 className="font-heading font-bold text-xl mt-1">Across team</h3>
          {topProducts.length === 0 && <div className="mt-6 text-sm text-muted-foreground">No bills yet — products will rank here.</div>}
          <div className="mt-4 space-y-2">
            {topProducts.slice(0, 6).map((p, i) => (
              <div key={p.name} className="flex items-center justify-between text-xs border-b border-border/50 py-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-muted-foreground">{String(i+1).padStart(2, "0")}</span>
                  <span className="font-semibold">{p.name}</span>
                </div>
                <span className="font-mono">{formatINR(p.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Performance cards */}
      {["ceo","admin","sales_manager"].includes(user.role) && (
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Trophy size={20} className="text-[hsl(var(--accent))]" weight="fill" />
            <h3 className="font-heading font-bold text-xl">Salespeople performance</h3>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {perf.map((p) => (
              <div key={p.id} className="border border-border rounded-md p-4 bg-card" data-testid={`perf-card-${p.id}`}>
                <div className="overline">{p.area || "—"}</div>
                <div className="font-heading font-bold text-base mt-1">{p.name}</div>
                <div className="mt-3 flex items-baseline justify-between">
                  <div>
                    <div className="overline">Actual</div>
                    <div className="font-mono font-bold">{formatINR(p.actual)}</div>
                  </div>
                  <div className="text-right">
                    <div className="overline">Target</div>
                    <div className="font-mono text-muted-foreground">{formatINR(p.target)}</div>
                  </div>
                </div>
                <div className="mt-3 h-1.5 rounded bg-muted overflow-hidden">
                  <div className={`h-full ${p.conversion_rate >= 80 ? "bg-emerald-500" : p.conversion_rate >= 50 ? "bg-amber-500" : "bg-red-500"}`}
                       style={{ width: `${Math.min(p.conversion_rate, 100)}%` }} />
                </div>
                <div className="mt-2 flex justify-between text-xs">
                  <span className="text-muted-foreground">Conversion</span>
                  <span className={`font-mono font-bold ${conversionColor(p.conversion_rate)}`}>{p.conversion_rate}%</span>
                </div>
                <div className="mt-3 pt-3 border-t border-border grid grid-cols-3 text-center gap-2">
                  <div><div className="text-[10px] uppercase text-muted-foreground">Visits</div><div className="font-mono font-bold text-sm">{p.visits}</div></div>
                  <div><div className="text-[10px] uppercase text-muted-foreground">Deals</div><div className="font-mono font-bold text-sm">{p.deals}</div></div>
                  <div><div className="text-[10px] uppercase text-muted-foreground">Won</div><div className="font-mono font-bold text-sm text-emerald-600">{p.won}</div></div>
                </div>
              </div>
            ))}
            {perf.length === 0 && <div className="col-span-full text-sm text-muted-foreground">No salespeople under your scope yet.</div>}
          </div>
        </div>
      )}

      {/* Live agent map */}
      {["ceo","admin","sales_manager"].includes(user.role) && (
        <div className="border border-border rounded-md bg-card overflow-hidden">
          <div className="p-4 border-b border-border flex items-center justify-between flex-wrap gap-2">
            <div>
              <div className="overline">Field signals</div>
              <h3 className="font-heading font-bold text-lg mt-0.5 flex items-center gap-2">
                <MapTrifold size={18} /> Live agent map
              </h3>
            </div>
            <div className="flex items-center gap-3 text-[10px] uppercase tracking-wider text-muted-foreground" data-testid="map-legend">
              <Legend color="#10b981" label="Last visit GPS" />
              <Legend color="#3b82f6" label="Live ping" />
              <Legend color="#a1a1aa" label="Area default" />
              <span className="font-mono">{agents.length} agents</span>
            </div>
          </div>
          <div style={{ height: 420 }}>
            <MapContainer center={[22.5, 78.9]} zoom={5} style={{ height: "100%", width: "100%" }} scrollWheelZoom={false}>
              <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {agents.map((a) => (
                <Marker key={a.salesperson_id} position={[a.lat, a.lng]} icon={agentIcon(a.source, a.role)}>
                  <Popup>
                    <div className="font-semibold text-sm">{a.name}</div>
                    <div className="text-[11px] text-zinc-500 capitalize">{a.role?.replace("_", " ")} · {a.area}</div>
                    <div className="text-[11px] mt-1">📍 {a.client}</div>
                    {a.last_seen && <div className="text-[10px] font-mono text-zinc-400">@ {new Date(a.last_seen).toLocaleString()}</div>}
                    {a.phone && <div className="text-[10px] font-mono">{a.phone}</div>}
                  </Popup>
                </Marker>
              ))}
              <FitBounds points={agents} />
            </MapContainer>
          </div>
          {agents.length === 0 && (
            <div className="p-4 text-xs text-muted-foreground text-center">No agents in scope yet.</div>
          )}
        </div>
      )}

      {/* Salesperson: Ping my location */}
      {user.role === "salesperson" && (
        <div className="mt-6 border border-border rounded-md p-4 md:p-5 bg-card flex flex-col md:flex-row gap-4 md:items-center justify-between">
          <div>
            <div className="overline">Field signal</div>
            <h3 className="font-heading font-bold mt-1">Ping my location</h3>
            <p className="text-xs text-muted-foreground mt-1 max-w-md">Broadcast your current GPS so your manager and HQ see your pin on the live map without needing a visit log.</p>
          </div>
          <Button
            data-testid="ping-location-btn"
            onClick={() => {
              if (!navigator.geolocation) return toast.error("Geolocation not supported");
              navigator.geolocation.getCurrentPosition(
                async (pos) => {
                  try {
                    await api.post("/users/me/ping-location", { lat: pos.coords.latitude, lng: pos.coords.longitude });
                    toast.success("Location pinged");
                  } catch { toast.error("Failed to broadcast"); }
                },
                () => toast.error("GPS permission denied")
              );
            }}
          >
            <Crosshair size={16} className="mr-1.5" weight="bold" /> Broadcast GPS now
          </Button>
        </div>
      )}
    </div>
  );
}

const Legend = ({ color, label }) => (
  <span className="inline-flex items-center gap-1.5">
    <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
    {label}
  </span>
);
