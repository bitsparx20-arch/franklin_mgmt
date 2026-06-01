import React, { useEffect, useState } from "react";
import api from "../lib/api";
import { PageHeader, EmptyState } from "../components/Common";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "../components/ui/sheet";
import { Badge } from "../components/ui/badge";
import { Plus, Trash, PencilSimple } from "@phosphor-icons/react";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import { formatINR } from "../lib/format";

export default function Products() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const canManage = ["ceo","admin"].includes(user.role);

  const load = async () => {
    const { data } = await api.get("/products");
    setItems(data);
  };
  useEffect(() => { load(); }, []);

  const del = async (id) => {
    if (!window.confirm("Delete this product?")) return;
    await api.delete(`/products/${id}`);
    toast.success("Deleted"); load();
  };

  return (
    <div>
      <PageHeader
        overline="Module 4"
        title="Product Catalogue"
        subtitle="Master price list — used when generating bills & GST invoices."
        actions={canManage && (
          <Sheet open={open} onOpenChange={(v) => { setOpen(v); if (!v) setEditing(null); }}>
            <SheetTrigger asChild>
              <Button data-testid="new-product-btn"><Plus size={16} className="mr-1.5" weight="bold" /> Add product</Button>
            </SheetTrigger>
            <SheetContent className="w-full sm:max-w-md">
              <ProductForm editing={editing} onClose={() => { setOpen(false); setEditing(null); load(); }} />
            </SheetContent>
          </Sheet>
        )}
      />

      {items.length === 0 ? <EmptyState>Add products to enable billing.</EmptyState> : (
        <div className="border border-border rounded-md overflow-x-auto bg-card">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left">
              <tr className="border-b border-border">
                <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold">SKU</th>
                <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold">Name</th>
                <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold">Category</th>
                <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold text-right">Unit Price</th>
                <th className="px-4 py-2.5 text-xs uppercase tracking-wider font-bold text-right">GST %</th>
                {canManage && <th className="px-4 py-2.5 text-xs"></th>}
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id} className="border-b border-border/50 hover:bg-muted/30" data-testid={`product-row-${p.id}`}>
                  <td className="px-4 py-2.5 font-mono text-xs">{p.sku}</td>
                  <td className="px-4 py-2.5 font-semibold">{p.name}</td>
                  <td className="px-4 py-2.5"><Badge variant="secondary">{p.category}</Badge></td>
                  <td className="px-4 py-2.5 font-mono text-right">{formatINR(p.unit_price)}</td>
                  <td className="px-4 py-2.5 font-mono text-right">{p.gst_percent}%</td>
                  {canManage && (
                    <td className="px-4 py-2.5 text-right">
                      <Button size="sm" variant="ghost" onClick={() => { setEditing(p); setOpen(true); }} data-testid={`product-edit-${p.id}`}><PencilSimple size={14} /></Button>
                      <Button size="sm" variant="ghost" onClick={() => del(p.id)} data-testid={`product-del-${p.id}`}><Trash size={14} /></Button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function ProductForm({ editing, onClose }) {
  const [form, setForm] = useState(editing || { name: "", sku: "", unit_price: 0, category: "", gst_percent: 18 });
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const payload = { ...form, unit_price: Number(form.unit_price), gst_percent: Number(form.gst_percent) };
      if (editing) await api.patch(`/products/${editing.id}`, payload);
      else await api.post("/products", payload);
      toast.success("Saved");
      onClose();
    } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); } finally { setBusy(false); }
  };
  return (
    <form onSubmit={submit} className="space-y-3 mt-4">
      <SheetHeader><SheetTitle className="font-heading">{editing ? "Edit" : "Add"} product</SheetTitle></SheetHeader>
      <div><Label>Name</Label><Input required value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} data-testid="product-name-input" /></div>
      <div><Label>SKU</Label><Input required value={form.sku} onChange={(e) => setForm({...form, sku: e.target.value})} data-testid="product-sku-input" /></div>
      <div><Label>Category</Label><Input value={form.category} onChange={(e) => setForm({...form, category: e.target.value})} /></div>
      <div className="grid grid-cols-2 gap-3">
        <div><Label>Unit price (₹)</Label><Input type="number" required value={form.unit_price} onChange={(e) => setForm({...form, unit_price: e.target.value})} data-testid="product-price-input" /></div>
        <div><Label>GST %</Label><Input type="number" value={form.gst_percent} onChange={(e) => setForm({...form, gst_percent: e.target.value})} /></div>
      </div>
      <Button type="submit" disabled={busy} className="w-full" data-testid="product-save-btn">{busy ? "Saving…" : "Save"}</Button>
    </form>
  );
}
