import React, { useState } from "react";
import api from "../lib/api";
import { PageHeader } from "../components/Common";
import { Button } from "../components/ui/button";
import { FilePdf, FileXls, ListBullets, Receipt, Funnel, Users, Phone, Star } from "@phosphor-icons/react";
import { toast } from "sonner";
import * as XLSX from "xlsx";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import { formatINR } from "../lib/format";
import { exportOverviewPDF } from "../lib/overviewPdf";

const REPORTS = [
  { key: "visits", label: "Visit Log", icon: ListBullets, endpoint: "/reports/visits",
    columns: ["client_name","client_type","location_text","visit_date","salesperson_name","status"] },
  { key: "bills", label: "Bill-wise Sales", icon: Receipt, endpoint: "/reports/bills",
    columns: ["invoice_no","client_name","salesperson_name","subtotal","gst_total","grand_total","created_at"] },
  { key: "pipeline", label: "Pipeline", icon: Funnel, endpoint: "/reports/pipeline",
    columns: ["client_name","client_type","area","stage","estimated_value","salesperson_name","next_follow_up"] },
  { key: "pocs", label: "POC contact list", icon: Phone, endpoint: "/reports/pocs",
    columns: ["client_name","poc_name","designation","mobile","email","area","salesperson_name"] },
];

export default function Reports() {
  const [busy, setBusy] = useState("");

  const exportExcel = async (r) => {
    setBusy(r.key + "_x");
    try {
      const { data } = await api.get(r.endpoint);
      if (!data.length) return toast.message("No data to export");
      const rows = data.map((d) => Object.fromEntries(r.columns.map((c) => [c, d[c] ?? ""])));
      const ws = XLSX.utils.json_to_sheet(rows);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, r.label.slice(0, 30));
      XLSX.writeFile(wb, `${r.key}_${Date.now()}.xlsx`);
      toast.success("Excel exported");
    } catch { toast.error("Failed"); } finally { setBusy(""); }
  };

  const exportPDF = async (r) => {
    setBusy(r.key + "_p");
    try {
      const { data } = await api.get(r.endpoint);
      if (!data.length) return toast.message("No data to export");
      const doc = new jsPDF({ orientation: "landscape" });
      doc.setFontSize(14); doc.setFont("helvetica", "bold");
      doc.text(`Franklin Wardcorpp · ${r.label}`, 14, 14);
      doc.setFontSize(8); doc.setFont("helvetica", "normal");
      doc.text(new Date().toLocaleString(), 14, 20);
      autoTable(doc, {
        startY: 24,
        head: [r.columns.map((c) => c.replace(/_/g, " ").toUpperCase())],
        body: data.map((d) => r.columns.map((c) => {
          const v = d[c];
          if (typeof v === "number" && c.includes("total")) return v.toFixed(2);
          if (typeof v === "string" && v.length > 35) return v.slice(0, 35) + "…";
          return v ?? "";
        })),
        headStyles: { fillColor: [9, 9, 11] },
        styles: { fontSize: 7 },
      });
      doc.save(`${r.key}_${Date.now()}.pdf`);
      toast.success("PDF exported");
    } catch { toast.error("Failed"); } finally { setBusy(""); }
  };

  return (
    <div>
      <PageHeader
        overline="Module 9"
        title="Reports & Exports"
        subtitle="Filtered exports as PDF & Excel. Powered by jsPDF + SheetJS."
        actions={
          <Button
            data-testid="overview-pdf-btn"
            onClick={async () => {
              setBusy("overview");
              try {
                const { data } = await api.get("/reports/overview");
                exportOverviewPDF(data);
                toast.success("Executive snapshot generated");
              } catch { toast.error("Failed to generate snapshot"); } finally { setBusy(""); }
            }}
            disabled={busy === "overview"}
            className="bg-foreground"
          >
            <Star size={16} weight="fill" className="mr-1.5 text-[hsl(var(--accent))]" />
            {busy === "overview" ? "Generating…" : "Executive snapshot PDF"}
          </Button>
        }
      />

      <div className="border border-border rounded-md bg-gradient-to-br from-zinc-900 to-zinc-950 text-white p-6 mb-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-[hsl(var(--accent))]/20 rounded-full -mr-12 -mt-12 blur-3xl" />
        <div className="relative">
          <div className="text-[10px] tracking-[0.2em] uppercase text-zinc-400">Featured</div>
          <h2 className="font-heading font-black text-2xl mt-1">Executive Snapshot</h2>
          <p className="text-sm text-zinc-300 mt-2 max-w-2xl">A 4-page beautifully formatted PDF: cover page, KPI grid, conversion funnel, pipeline by stage, top performers, target vs actual, 12-month revenue trend, top products and recent invoices.</p>
        </div>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {REPORTS.map((r) => (
          <div key={r.key} className="border border-border rounded-md p-5 bg-card" data-testid={`report-${r.key}`}>
            <r.icon size={24} className="text-[hsl(var(--accent))]" />
            <h3 className="font-heading font-bold mt-3 text-base">{r.label}</h3>
            <p className="text-xs text-muted-foreground mt-1">{r.columns.length} columns · filtered by your role scope</p>
            <div className="mt-4 flex gap-2">
              <Button size="sm" variant="outline" disabled={busy === r.key + "_x"} onClick={() => exportExcel(r)} data-testid={`report-excel-${r.key}`}><FileXls size={14} className="mr-1.5" weight="bold" /> Excel</Button>
              <Button size="sm" disabled={busy === r.key + "_p"} onClick={() => exportPDF(r)} data-testid={`report-pdf-${r.key}`}><FilePdf size={14} className="mr-1.5" weight="bold" /> PDF</Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
