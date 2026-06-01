import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

const ACCENT = [255, 84, 0];
const INK = [9, 9, 11];
const GREY = [113, 113, 122];
const LIGHT = [244, 244, 245];
const GREEN = [16, 185, 129];
const AMBER = [245, 158, 11];
const RED = [220, 38, 38];

const fmtINR = (n) => `Rs. ${(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
const fmtDate = (d) => new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });

export function exportOverviewPDF(data) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const W = doc.internal.pageSize.getWidth();
  const H = doc.internal.pageSize.getHeight();

  // ============ COVER ============
  doc.setFillColor(...INK);
  doc.rect(0, 0, W, H, "F");
  doc.setFillColor(...ACCENT);
  doc.rect(0, 0, 8, H, "F");

  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10);
  doc.text("FRANKLIN WARDCORPP", 40, 80);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.setTextColor(180, 180, 180);
  doc.text("SALES INTELLIGENCE OS", 40, 92);

  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(48);
  doc.text("Executive", 40, 280);
  doc.text("Snapshot", 40, 332);

  doc.setFillColor(...ACCENT);
  doc.rect(40, 350, 80, 4, "F");

  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  doc.setTextColor(220, 220, 220);
  doc.text(`Prepared for ${data.actor.name} (${data.actor.role.toUpperCase()})`, 40, 380);
  doc.text(`Generated ${fmtDate(data.generated_at)}`, 40, 396);

  // Big headline number
  const totals = data.overview?.totals || {};
  doc.setFont("helvetica", "bold");
  doc.setFontSize(60);
  doc.setTextColor(...ACCENT);
  doc.text(fmtINR(totals.revenue), 40, 540);
  doc.setFontSize(10);
  doc.setTextColor(180, 180, 180);
  doc.setFont("helvetica", "normal");
  doc.text("BILLED REVENUE TO DATE", 40, 558);

  // Mini grid
  const miniStats = [
    { label: "VISITS", v: totals.visits ?? 0 },
    { label: "POCS", v: totals.pocs ?? 0 },
    { label: "DEALS", v: totals.deals ?? 0 },
    { label: "WON", v: totals.won ?? 0 },
  ];
  miniStats.forEach((s, i) => {
    const x = 40 + i * 130;
    doc.setFont("helvetica", "bold");
    doc.setFontSize(28);
    doc.setTextColor(255, 255, 255);
    doc.text(String(s.v), x, 660);
    doc.setFontSize(8);
    doc.setTextColor(180, 180, 180);
    doc.setFont("helvetica", "normal");
    doc.text(s.label, x, 678);
  });

  // Footer
  doc.setFontSize(7);
  doc.setTextColor(120, 120, 120);
  doc.text("CONFIDENTIAL · INTERNAL DISTRIBUTION", 40, H - 40);

  // ============ PAGE 2 — KPI Grid + Funnel ============
  doc.addPage();
  pageHeader(doc, W, "01 · Key Performance Indicators");

  // KPI cards (2x3 grid)
  const kpis = [
    { l: "Visits", v: totals.visits ?? 0, sub: "Field logs" },
    { l: "POCs Captured", v: totals.pocs ?? 0, sub: "Decision makers" },
    { l: "Deals", v: totals.deals ?? 0, sub: "All stages" },
    { l: "Won", v: totals.won ?? 0, sub: "Closed-Won", color: GREEN },
    { l: "Pipeline Value", v: fmtINR(totals.pipeline_value), sub: "Excl. lost", color: ACCENT },
    { l: "Billed Revenue", v: fmtINR(totals.revenue), sub: "Total", color: GREEN },
  ];

  const cardW = (W - 80 - 24) / 3;
  const cardH = 90;
  kpis.forEach((k, i) => {
    const x = 40 + (i % 3) * (cardW + 12);
    const y = 140 + Math.floor(i / 3) * (cardH + 12);
    doc.setFillColor(...LIGHT);
    doc.rect(x, y, cardW, cardH, "F");
    doc.setFillColor(...(k.color || INK));
    doc.rect(x, y, 4, cardH, "F");
    doc.setTextColor(...GREY);
    doc.setFontSize(7);
    doc.setFont("helvetica", "bold");
    doc.text(k.l.toUpperCase(), x + 14, y + 20);
    doc.setTextColor(...INK);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(typeof k.v === "string" && k.v.length > 8 ? 16 : 22);
    doc.text(String(k.v), x + 14, y + 52);
    doc.setTextColor(...GREY);
    doc.setFontSize(8);
    doc.setFont("helvetica", "normal");
    doc.text(k.sub, x + 14, y + 72);
  });

  // Funnel chart (horizontal bars)
  const funnel = data.funnel?.stages || [];
  const fStart = 360;
  doc.setTextColor(...INK);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(13);
  doc.text("Conversion funnel", 40, fStart);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.setTextColor(...GREY);
  doc.text("Visits → POCs → Pipeline → Won", 40, fStart + 14);

  const maxF = Math.max(...funnel.map((s) => s.value), 1);
  funnel.forEach((s, i) => {
    const y = fStart + 40 + i * 38;
    const w = (W - 200) * (s.value / maxF);
    const colors = [GREY, [59, 130, 246], AMBER, GREEN];
    doc.setFillColor(...(colors[i] || GREY));
    doc.rect(40, y, Math.max(w, 6), 24, "F");
    doc.setTextColor(...INK);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.text(s.label, 40, y - 4);
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(11);
    if (w > 30) doc.text(String(s.value), 50, y + 16);
    else { doc.setTextColor(...INK); doc.text(String(s.value), 40 + w + 6, y + 16); }
  });

  pageFooter(doc, W, H, "Page 2");

  // ============ PAGE 3 — Pipeline by stage + Top performers ============
  doc.addPage();
  pageHeader(doc, W, "02 · Pipeline & Performance");

  const stages = data.overview?.stages_summary || {};
  doc.setTextColor(...INK);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(13);
  doc.text("Kanban pipeline by stage", 40, 140);
  autoTable(doc, {
    startY: 154,
    head: [["Stage", "Deals", "Value"]],
    body: Object.entries(stages).map(([s, info]) => [
      s.replace("_", " "), info.count, fmtINR(info.value),
    ]),
    theme: "plain",
    headStyles: { fillColor: INK, textColor: [255, 255, 255], fontSize: 9 },
    bodyStyles: { fontSize: 9, lineColor: [228, 228, 231], lineWidth: 0.5 },
    columnStyles: { 1: { halign: "center" }, 2: { halign: "right", fontStyle: "bold" } },
    margin: { left: 40, right: W / 2 + 10 },
  });

  // Top performers (right side)
  doc.setTextColor(...INK);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(13);
  doc.text("Top performers", W / 2 + 20, 140);
  const sortedPerf = [...(data.performance || [])].sort((a, b) => b.conversion_rate - a.conversion_rate).slice(0, 6);
  autoTable(doc, {
    startY: 154,
    head: [["Salesperson", "Area", "Conv. %"]],
    body: sortedPerf.map((p) => [p.name, p.area || "—", `${p.conversion_rate}%`]),
    theme: "plain",
    headStyles: { fillColor: INK, textColor: [255, 255, 255], fontSize: 9 },
    bodyStyles: { fontSize: 9, lineColor: [228, 228, 231], lineWidth: 0.5 },
    columnStyles: { 2: { halign: "right", fontStyle: "bold" } },
    margin: { left: W / 2 + 20, right: 40 },
  });

  // Per-salesperson target vs actual bar
  let y = Math.max(doc.lastAutoTable.finalY, 290) + 30;
  doc.setFont("helvetica", "bold");
  doc.setFontSize(13);
  doc.text("Target vs Actual", 40, y);

  const perf = data.performance || [];
  y += 14;
  perf.slice(0, 8).forEach((p) => {
    const max = Math.max(p.target, p.actual, 1);
    const trackW = W - 80 - 130;
    doc.setTextColor(...INK);
    doc.setFontSize(9);
    doc.setFont("helvetica", "bold");
    doc.text(p.name, 40, y + 12);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(...GREY);
    doc.setFontSize(8);
    doc.text(p.area || "—", 40, y + 24);

    // Track
    doc.setFillColor(230, 230, 230);
    doc.rect(140, y + 4, trackW, 10, "F");
    // Target marker
    const tgtW = (p.target / max) * trackW;
    doc.setFillColor(...GREY);
    doc.rect(140, y + 4, tgtW, 10, "F");
    // Actual
    const actW = (p.actual / max) * trackW;
    const colorActual = p.conversion_rate >= 80 ? GREEN : p.conversion_rate >= 50 ? AMBER : RED;
    doc.setFillColor(...colorActual);
    doc.rect(140, y + 4, Math.max(actW, 2), 10, "F");

    doc.setTextColor(...INK);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.text(`${p.conversion_rate}%`, W - 40, y + 12, { align: "right" });
    y += 28;
  });

  pageFooter(doc, W, H, "Page 3");

  // ============ PAGE 4 — Revenue trend + Top products ============
  doc.addPage();
  pageHeader(doc, W, "03 · Revenue & Product Mix");

  // 12-month line chart
  const months = data.overview?.monthly_revenue || [];
  doc.setTextColor(...INK);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(13);
  doc.text("Month-over-month revenue", 40, 140);
  const chartX = 40, chartY = 160, chartW = W - 80, chartH = 180;
  doc.setDrawColor(...LIGHT);
  doc.setLineWidth(0.5);
  // Grid lines
  for (let i = 0; i <= 4; i++) {
    const gy = chartY + (i * chartH) / 4;
    doc.line(chartX, gy, chartX + chartW, gy);
  }
  const maxR = Math.max(...months.map((m) => m.revenue), 1);
  doc.setDrawColor(...ACCENT);
  doc.setLineWidth(2);
  let prevX = null, prevY = null;
  months.forEach((m, i) => {
    const px = chartX + (i / Math.max(months.length - 1, 1)) * chartW;
    const py = chartY + chartH - (m.revenue / maxR) * chartH;
    if (prevX !== null) doc.line(prevX, prevY, px, py);
    doc.setFillColor(...ACCENT);
    doc.circle(px, py, 2.5, "F");
    prevX = px; prevY = py;
  });
  // X labels (skip)
  doc.setFontSize(7);
  doc.setTextColor(...GREY);
  months.forEach((m, i) => {
    if (i % 2 !== 0) return;
    const px = chartX + (i / Math.max(months.length - 1, 1)) * chartW;
    doc.text(m.month.slice(5), px - 6, chartY + chartH + 12);
  });

  // Top products
  const products = data.top_products || [];
  doc.setTextColor(...INK);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(13);
  doc.text("Top-selling products", 40, 400);
  autoTable(doc, {
    startY: 414,
    head: [["#", "Product", "Revenue"]],
    body: products.slice(0, 10).map((p, i) => [String(i + 1).padStart(2, "0"), p.name, fmtINR(p.value)]),
    theme: "plain",
    headStyles: { fillColor: INK, textColor: [255, 255, 255], fontSize: 9 },
    bodyStyles: { fontSize: 9, lineColor: [228, 228, 231], lineWidth: 0.5 },
    columnStyles: { 0: { cellWidth: 30, halign: "center" }, 2: { halign: "right", fontStyle: "bold" } },
    margin: { left: 40, right: 40 },
  });

  // Recent bills
  const bills = data.recent_bills || [];
  if (bills.length) {
    let y2 = doc.lastAutoTable.finalY + 30;
    doc.setTextColor(...INK);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(13);
    doc.text("Recent invoices", 40, y2);
    autoTable(doc, {
      startY: y2 + 14,
      head: [["Invoice", "Client", "Date", "Total"]],
      body: bills.map((b) => [b.invoice_no, b.client_name, fmtDate(b.created_at), fmtINR(b.grand_total)]),
      theme: "plain",
      headStyles: { fillColor: INK, textColor: [255, 255, 255], fontSize: 9 },
      bodyStyles: { fontSize: 9, lineColor: [228, 228, 231], lineWidth: 0.5 },
      columnStyles: { 3: { halign: "right", fontStyle: "bold" } },
      margin: { left: 40, right: 40 },
    });
  }

  pageFooter(doc, W, H, "Page 4");

  doc.save(`franklin_overview_${Date.now()}.pdf`);
}

function pageHeader(doc, W, title) {
  doc.setFillColor(...INK);
  doc.rect(0, 0, W, 60, "F");
  doc.setFillColor(...ACCENT);
  doc.rect(0, 60, W, 3, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("FRANKLIN WARDCORPP · EXECUTIVE SNAPSHOT", 40, 28);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(14);
  doc.text(title, 40, 48);
}

function pageFooter(doc, W, H, label) {
  doc.setDrawColor(...LIGHT);
  doc.setLineWidth(0.5);
  doc.line(40, H - 36, W - 40, H - 36);
  doc.setTextColor(...GREY);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(7);
  doc.text("CONFIDENTIAL · For internal review only", 40, H - 22);
  doc.text(label, W - 40, H - 22, { align: "right" });
}
