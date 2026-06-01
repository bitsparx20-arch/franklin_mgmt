import React, { useEffect, useState, useMemo } from "react";
import api from "../lib/api";
import { PageHeader, EmptyState, StatCard } from "../components/Common";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "../components/ui/sheet";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Plus, FilePdf, Trash } from "@phosphor-icons/react";
import { toast } from "sonner";
import { formatINR, formatDate } from "../lib/format";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

export default function Bills() {
  const [bills, setBills] = useState([]);
  const [open, setOpen] = useState(false);

  const load = async () => {
    const { data } = await api.get("/bills");
    setBills(data);
  };
  useEffect(() => { load(); }, []);

  const totalRevenue = bills.reduce((a, b) => a + (b.grand_total || 0), 0);

  return (
    <div>
      <PageHeader
        overline="Module 4"
        title="Bills & Invoices"
        subtitle="GST-compliant invoices. Generated from products. Export as PDF."
        actions={
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button data-testid="new-bill-btn"><Plus size={16} className="mr-1.5" weight="bold" /> Generate bill</Button>
            </SheetTrigger>
            <SheetContent className="overflow-y-auto w-full sm:max-w-2xl">
              <BillForm onClose={() => { setOpen(false); load(); }} />
            </SheetContent>
          </Sheet>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
        <StatCard label="Total bills" value={bills.length} />
        <StatCard label="Total revenue" value={formatINR(totalRevenue)} accent="text-emerald-600 dark:text-emerald-400" />
        <StatCard label="Need approval" value={bills.filter(b => b.needs_approval).length} accent="text-amber-600" />
      </div>

      {bills.length === 0 ? <EmptyState>Generate your first bill after a sale.</EmptyState> : (
        <div className="border border-border rounded-md overflow-x-auto bg-card">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left">
              <tr className="border-b border-border">
                <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold">Invoice</th>
                <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold">Client</th>
                <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold">Date</th>
                <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold">Items</th>
                <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold text-right">Subtotal</th>
                <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold text-right">GST</th>
                <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold text-right">Total</th>
                <th className="px-4 py-2.5 text-xs"></th>
              </tr>
            </thead>
            <tbody>
              {bills.map((b) => (
                <tr key={b.id} className="border-b border-border/50 hover:bg-muted/30" data-testid={`bill-row-${b.id}`}>
                  <td className="px-4 py-2.5 font-mono text-xs">{b.invoice_no}</td>
                  <td className="px-4 py-2.5 font-semibold">
                    {b.client_name}
                    {b.needs_approval && <Badge className="ml-2 bg-amber-500">Approval</Badge>}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs">{formatDate(b.created_at)}</td>
                  <td className="px-4 py-2.5 text-xs">{b.lines.length}</td>
                  <td className="px-4 py-2.5 font-mono text-right">{formatINR(b.subtotal)}</td>
                  <td className="px-4 py-2.5 font-mono text-right">{formatINR(b.gst_total)}</td>
                  <td className="px-4 py-2.5 font-mono text-right font-bold">{formatINR(b.grand_total)}</td>
                  <td className="px-4 py-2.5">
                    <Button size="sm" variant="outline" onClick={() => exportBillPDF(b)} data-testid={`bill-pdf-${b.id}`}><FilePdf size={14} className="mr-1" />PDF</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function BillForm({ onClose }) {
  const [products, setProducts] = useState([]);
  const [client_name, setClientName] = useState("");
  const [discount, setDiscount] = useState(0);
  const [lines, setLines] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/products").then((r) => setProducts(r.data));
  }, []);

  const addLine = (productId) => {
    const p = products.find((x) => x.id === productId);
    if (!p) return;
    setLines((ls) => [...ls, {
      product_id: p.id, product_name: p.name, sku: p.sku,
      quantity: 1, unit_price: p.unit_price, gst_percent: p.gst_percent,
    }]);
  };
  const updateLine = (i, field, val) => {
    setLines((ls) => ls.map((l, idx) => idx === i ? { ...l, [field]: field === "quantity" || field === "unit_price" ? Number(val) : val } : l));
  };
  const removeLine = (i) => setLines((ls) => ls.filter((_, idx) => idx !== i));

  const totals = useMemo(() => {
    let subtotal = 0, gst = 0;
    lines.forEach((l) => {
      const amt = l.quantity * l.unit_price;
      subtotal += amt;
      gst += amt * (l.gst_percent / 100);
    });
    const disc = subtotal * (discount / 100);
    return { subtotal, gst, discount: disc, grand: subtotal - disc + gst };
  }, [lines, discount]);

  const submit = async (e) => {
    e.preventDefault();
    if (lines.length === 0) return toast.error("Add at least one product");
    setBusy(true);
    try {
      await api.post("/bills", {
        client_name, lines, discount_percent: Number(discount),
      });
      toast.success("Bill generated");
      onClose();
    } catch { toast.error("Failed"); } finally { setBusy(false); }
  };

  return (
    <form onSubmit={submit} className="space-y-4 mt-4">
      <SheetHeader><SheetTitle className="font-heading">Generate bill</SheetTitle></SheetHeader>
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2"><Label>Client name</Label><Input required value={client_name} onChange={(e) => setClientName(e.target.value)} data-testid="bill-client-input" /></div>
        <div>
          <Label>Add product</Label>
          <Select onValueChange={addLine}>
            <SelectTrigger data-testid="bill-product-select"><SelectValue placeholder="Pick product" /></SelectTrigger>
            <SelectContent>{products.map((p) => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}</SelectContent>
          </Select>
        </div>
        <div><Label>Discount %</Label><Input type="number" value={discount} onChange={(e) => setDiscount(e.target.value)} /></div>
      </div>

      {lines.length === 0 ? (
        <div className="border border-dashed border-border rounded p-6 text-center text-xs text-muted-foreground">No products added.</div>
      ) : (
        <div className="border border-border rounded-md">
          <table className="w-full text-xs">
            <thead className="bg-muted/50">
              <tr className="border-b border-border">
                <th className="px-2 py-2 text-left">Item</th>
                <th className="px-2 py-2">Qty</th>
                <th className="px-2 py-2">Price</th>
                <th className="px-2 py-2 text-right">Amount</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {lines.map((l, i) => (
                <tr key={i} className="border-b border-border/50">
                  <td className="px-2 py-2">{l.product_name} <span className="font-mono text-muted-foreground text-[10px]">({l.sku})</span></td>
                  <td className="px-2 py-1"><Input className="h-7 w-16" type="number" value={l.quantity} onChange={(e) => updateLine(i, "quantity", e.target.value)} /></td>
                  <td className="px-2 py-1"><Input className="h-7 w-20" type="number" value={l.unit_price} onChange={(e) => updateLine(i, "unit_price", e.target.value)} /></td>
                  <td className="px-2 py-2 text-right font-mono">{formatINR(l.quantity * l.unit_price)}</td>
                  <td className="px-2 py-1"><Button size="sm" type="button" variant="ghost" onClick={() => removeLine(i)}><Trash size={12} /></Button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="border-t border-border pt-3 space-y-1 text-sm">
        <Row label="Subtotal" v={totals.subtotal} />
        <Row label={`Discount (${discount}%)`} v={-totals.discount} />
        <Row label="GST" v={totals.gst} />
        <div className="flex justify-between font-mono font-bold text-base pt-2 border-t border-border">
          <span>Grand Total</span><span>{formatINR(totals.grand)}</span>
        </div>
      </div>

      <Button type="submit" disabled={busy} className="w-full" data-testid="bill-save-btn">{busy ? "Saving…" : "Generate bill"}</Button>
    </form>
  );
}

const Row = ({ label, v }) => (
  <div className="flex justify-between font-mono text-xs">
    <span>{label}</span><span>{formatINR(v)}</span>
  </div>
);

export function exportBillPDF(b) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const W = doc.internal.pageSize.getWidth(); // 595pt
  const H = doc.internal.pageSize.getHeight(); // 842pt
  const ACCENT = [255, 84, 0];
  const INK = [9, 9, 11];
  const GREY = [113, 113, 122];
  const LIGHT = [244, 244, 245];

  // Header band
  doc.setFillColor(...INK);
  doc.rect(0, 0, W, 110, "F");
  doc.setFillColor(...ACCENT);
  doc.rect(0, 105, W, 5, "F");

  // Brand
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(22);
  doc.text("FRANKLIN WARDCORPP", 40, 50);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.setTextColor(200, 200, 200);
  doc.text("INDUSTRIAL FASTENERS · STEEL · FABRICATION SUPPLIES", 40, 64);
  doc.setFontSize(7);
  doc.text("Sales Intelligence OS · GST Invoice", 40, 76);

  // Invoice meta (right)
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10);
  doc.text("TAX INVOICE", W - 40, 40, { align: "right" });
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.text(`Invoice No: ${b.invoice_no}`, W - 40, 56, { align: "right" });
  doc.text(`Date: ${formatDate(b.created_at)}`, W - 40, 68, { align: "right" });
  doc.text(`Issued by: ${b.salesperson_name}`, W - 40, 80, { align: "right" });

  // Billed-to block
  let y = 145;
  doc.setTextColor(...GREY);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(8);
  doc.text("BILLED TO", 40, y);
  doc.setTextColor(...INK);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(14);
  doc.text(b.client_name, 40, y + 18);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(...GREY);
  if (b.notes) doc.text(b.notes.slice(0, 80), 40, y + 32);

  // Status pill
  doc.setFillColor(...(b.needs_approval ? [251, 191, 36] : [16, 185, 129]));
  doc.roundedRect(W - 130, y, 90, 22, 11, 11, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(8);
  doc.text(b.needs_approval ? "NEEDS APPROVAL" : "STANDARD", W - 85, y + 14, { align: "center" });

  // Line items table
  autoTable(doc, {
    startY: y + 50,
    head: [["#", "SKU", "Description", "Qty", "Unit Price", "GST %", "Amount"]],
    body: b.lines.map((l, i) => [
      String(i + 1).padStart(2, "0"),
      l.sku,
      l.product_name,
      l.quantity,
      `Rs. ${l.unit_price.toFixed(2)}`,
      `${l.gst_percent}%`,
      `Rs. ${(l.quantity * l.unit_price).toFixed(2)}`,
    ]),
    theme: "plain",
    headStyles: {
      fillColor: INK, textColor: [255, 255, 255], fontStyle: "bold",
      fontSize: 8, halign: "left", cellPadding: { top: 8, right: 6, bottom: 8, left: 8 },
    },
    bodyStyles: {
      fontSize: 9, cellPadding: { top: 9, right: 6, bottom: 9, left: 8 },
      lineColor: [228, 228, 231], lineWidth: 0.5,
    },
    alternateRowStyles: { fillColor: [250, 250, 250] },
    columnStyles: {
      0: { cellWidth: 24, halign: "center" },
      1: { cellWidth: 70, fontStyle: "bold" },
      3: { halign: "center", cellWidth: 40 },
      4: { halign: "right", cellWidth: 70 },
      5: { halign: "center", cellWidth: 50 },
      6: { halign: "right", cellWidth: 75, fontStyle: "bold" },
    },
    margin: { left: 40, right: 40 },
  });

  let yFinal = doc.lastAutoTable.finalY + 18;

  // Totals panel
  const boxX = W - 240, boxW = 200;
  doc.setFillColor(...LIGHT);
  doc.rect(boxX, yFinal, boxW, 110, "F");
  doc.setDrawColor(...INK);
  doc.setLineWidth(0.5);
  doc.line(boxX, yFinal, boxX + boxW, yFinal);

  const rowL = (label, val, dy, bold = false) => {
    doc.setTextColor(...GREY);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.text(label, boxX + 12, yFinal + dy);
    doc.setTextColor(...INK);
    doc.setFont("helvetica", bold ? "bold" : "normal");
    doc.setFontSize(bold ? 11 : 9);
    doc.text(val, boxX + boxW - 12, yFinal + dy, { align: "right" });
  };

  rowL("Subtotal", `Rs. ${b.subtotal.toFixed(2)}`, 18);
  rowL(`Discount (${b.discount_percent}%)`, `- Rs. ${b.discount_amount.toFixed(2)}`, 36);
  rowL("GST", `Rs. ${b.gst_total.toFixed(2)}`, 54);

  // Grand total accent strip
  doc.setFillColor(...INK);
  doc.rect(boxX, yFinal + 70, boxW, 40, "F");
  doc.setFillColor(...ACCENT);
  doc.rect(boxX, yFinal + 70, 4, 40, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.text("GRAND TOTAL", boxX + 14, yFinal + 88);
  doc.setFontSize(16);
  doc.text(`Rs. ${b.grand_total.toFixed(2)}`, boxX + boxW - 12, yFinal + 96, { align: "right" });

  // Footer
  doc.setTextColor(...GREY);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.text("Thank you for choosing Franklin Wardcorpp.", 40, H - 60);
  doc.setFontSize(7);
  doc.text("Payment terms: NET 30 · Bank: Franklin Wardcorpp Pvt Ltd · A/C: XXXX-XXXX · Helpdesk: ops@franklinwardcorpp.com", 40, H - 46);

  // Bottom accent strip
  doc.setFillColor(...ACCENT);
  doc.rect(0, H - 24, W, 24, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(7);
  doc.text(`FRANKLIN WARDCORPP   ·   ${b.invoice_no}   ·   Page 1 of 1`, W / 2, H - 9, { align: "center" });

  doc.save(`${b.invoice_no}.pdf`);
}
