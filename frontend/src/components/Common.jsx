import React from "react";

export const PageHeader = ({ overline, title, subtitle, actions }) => (
  <div className="mb-6 md:mb-8 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
    <div>
      <div className="overline">{overline}</div>
      <h1 className="font-heading font-black text-3xl md:text-4xl tracking-tighter mt-1">{title}</h1>
      {subtitle && <p className="text-sm text-muted-foreground mt-1.5 max-w-xl">{subtitle}</p>}
    </div>
    {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
  </div>
);

export const StatCard = ({ label, value, sub, accent }) => (
  <div className="border border-border rounded-md p-4 md:p-5 bg-card">
    <div className="overline">{label}</div>
    <div className={`mt-2 font-mono text-2xl md:text-3xl tracking-tight font-bold ${accent || ""}`}>{value}</div>
    {sub && <div className="text-xs text-muted-foreground mt-1">{sub}</div>}
  </div>
);

export const EmptyState = ({ children }) => (
  <div className="border border-dashed border-border rounded-md p-10 text-center">
    <div className="overline mb-2">No data yet</div>
    <div className="text-sm text-muted-foreground">{children}</div>
  </div>
);
