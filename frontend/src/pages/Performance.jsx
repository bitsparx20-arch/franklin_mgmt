import React, { useEffect, useState } from "react";
import api from "../lib/api";
import { PageHeader, EmptyState } from "../components/Common";
import { formatINR, conversionColor } from "../lib/format";
import { Trophy, TrendDown, TrendUp } from "@phosphor-icons/react";
import { Progress } from "../components/ui/progress";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export default function Performance() {
  const [perf, setPerf] = useState([]);
  useEffect(() => {
    api.get("/dashboard/performance").then((r) => setPerf(r.data));
  }, []);

  const sorted = [...perf].sort((a, b) => b.conversion_rate - a.conversion_rate);
  const top = sorted.slice(0, 3);
  const under = sorted.slice(-3).reverse();

  return (
    <div>
      <PageHeader
        overline="Module 5"
        title="Sales Performance"
        subtitle="Per-salesperson targets, actuals, conversion rates, product mix."
      />

      {perf.length === 0 ? <EmptyState>No salespeople tracked yet.</EmptyState> : (
        <>
          <div className="grid lg:grid-cols-2 gap-4 md:gap-6 mb-8">
            <Panel title="Top performers" icon={<Trophy weight="fill" className="text-amber-500" />}>
              {top.map((p) => <RankRow key={p.id} sp={p} good />)}
            </Panel>
            <Panel title="Needs attention" icon={<TrendDown weight="bold" className="text-red-500" />}>
              {under.map((p) => <RankRow key={p.id} sp={p} />)}
            </Panel>
          </div>

          <div className="border border-border rounded-md bg-card overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left">
                <tr className="border-b border-border">
                  <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold">Salesperson</th>
                  <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold">Area</th>
                  <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold text-right">Target</th>
                  <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold text-right">Actual</th>
                  <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold text-right">Conv.</th>
                  <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold text-right">Pipeline %</th>
                  <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold text-right">Visits</th>
                </tr>
              </thead>
              <tbody>
                {perf.map((p) => (
                  <tr key={p.id} className="border-b border-border/50 hover:bg-muted/30" data-testid={`perf-row-${p.id}`}>
                    <td className="px-4 py-3 font-semibold">{p.name}</td>
                    <td className="px-4 py-3 text-xs">{p.area || "—"}</td>
                    <td className="px-4 py-3 font-mono text-right">{formatINR(p.target)}</td>
                    <td className="px-4 py-3 font-mono text-right font-bold">{formatINR(p.actual)}</td>
                    <td className={`px-4 py-3 font-mono text-right ${conversionColor(p.conversion_rate)}`}>{p.conversion_rate}%</td>
                    <td className="px-4 py-3 font-mono text-right">{p.pipeline_conversion}%</td>
                    <td className="px-4 py-3 font-mono text-right">{p.visits}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-8 border border-border rounded-md p-6 bg-card">
            <div className="overline">Per-salesperson actual revenue</div>
            <h3 className="font-heading font-bold text-xl mt-1 mb-4">Comparison</h3>
            <div style={{ height: 280 }}>
              <ResponsiveContainer>
                <BarChart data={perf}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => v >= 100000 ? `${(v/100000).toFixed(1)}L` : v} />
                  <Tooltip formatter={(v) => formatINR(v)} contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", fontSize: 12 }}/>
                  <Bar dataKey="actual" fill="hsl(var(--accent))" radius={[4,4,0,0]} />
                  <Bar dataKey="target" fill="hsl(var(--muted-foreground))" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

const Panel = ({ title, icon, children }) => (
  <div className="border border-border rounded-md p-4 bg-card">
    <div className="flex items-center gap-2 mb-3">
      {icon}<h3 className="font-heading font-bold text-base">{title}</h3>
    </div>
    <div className="space-y-2">{children}</div>
  </div>
);

const RankRow = ({ sp, good }) => (
  <div className="flex items-center gap-3 p-2 rounded border border-border/50">
    <div className="font-mono text-2xl text-muted-foreground">{good ? <TrendUp size={20} className="text-emerald-500" /> : <TrendDown size={20} className="text-red-500" />}</div>
    <div className="flex-1">
      <div className="text-sm font-bold">{sp.name}</div>
      <div className="text-[10px] text-muted-foreground">{sp.area}</div>
    </div>
    <div className={`font-mono font-bold text-sm ${conversionColor(sp.conversion_rate)}`}>{sp.conversion_rate}%</div>
  </div>
);
