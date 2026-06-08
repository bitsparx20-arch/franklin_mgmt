import React, { useEffect, useState } from "react";
import api from "../lib/api";
import { PageHeader, EmptyState } from "../components/Common";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "../components/ui/sheet";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Plus, Trash, UserCircle, PencilSimple } from "@phosphor-icons/react";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import { ROLE_LABEL, formatINR } from "../lib/format";

const ROLE_RANK = { ceo: 4, admin: 3, sales_manager: 2, salesperson: 1 };

export default function Employees() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [managers, setManagers] = useState([]);
  const [open, setOpen] = useState(false);
  const [editUser, setEditUser] = useState(null);

  const load = async () => {
    const { data } = await api.get("/users");
    setUsers(data);
    setManagers(data.filter((u) => ["admin", "sales_manager", "ceo"].includes(u.role)));
  };
  useEffect(() => { load(); }, []);

  const canEdit = (target) => {
    if (target.id === user.id) return true;
    return (ROLE_RANK[user.role] || 0) > (ROLE_RANK[target.role] || 0);
  };

  const del = async (id) => {
    if (!window.confirm("Delete employee?")) return;
    try {
      await api.delete(`/users/${id}`);
      toast.success("Deleted");
      load();
    } catch { toast.error("Failed"); }
  };

  const openEdit = (u) => {
    setEditUser(u);
    setOpen(true);
  };

  const closeSheet = () => {
    setOpen(false);
    setEditUser(null);
  };

  return (
    <div>
      <PageHeader
        overline="Module 7"
        title="Employees"
        subtitle="CEO → Admin → Sales Manager → Salesperson. Role-aware CRUD."
        actions={
          <Sheet open={open} onOpenChange={(v) => { if (!v) closeSheet(); else setOpen(true); }}>
            <SheetTrigger asChild>
              <Button data-testid="new-emp-btn" onClick={() => setEditUser(null)}>
                <Plus size={16} className="mr-1.5" weight="bold" /> Add employee
              </Button>
            </SheetTrigger>
            <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
              <EmpForm
                key={editUser?.id || "new"}
                employee={editUser}
                managers={managers}
                role={user.role}
                onClose={() => { closeSheet(); load(); }}
              />
            </SheetContent>
          </Sheet>
        }
      />

      {users.length === 0 ? <EmptyState>No employees yet.</EmptyState> : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {users.map((u) => (
            <div key={u.id} className="border border-border rounded-md p-4 bg-card" data-testid={`emp-card-${u.id}`}>
              <div className="flex items-start gap-3">
                <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                  {u.photo_url ? <img src={u.photo_url} className="h-12 w-12 rounded-full object-cover" alt="" /> : <UserCircle size={32} className="text-muted-foreground" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-heading font-bold text-sm">{u.name}</div>
                  <div className="text-xs text-muted-foreground truncate">{u.designation || ROLE_LABEL[u.role]}</div>
                  <Badge variant="secondary" className="mt-1 text-[10px]">{ROLE_LABEL[u.role]}</Badge>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-border/60 grid grid-cols-2 gap-2 text-xs">
                <div><div className="overline">Area</div><div>{u.area || "—"}</div></div>
                <div><div className="overline">Target</div><div className="font-mono">{formatINR(u.target || 0)}</div></div>
                <div className="col-span-2"><div className="overline">Phone</div><div className="font-mono">{u.phone || "—"}</div></div>
                <div className="col-span-2"><div className="overline">Email</div><div className="font-mono text-[10px] truncate">{u.email}</div></div>
              </div>
              <div className="mt-2 flex gap-2">
                {canEdit(u) && (
                  <Button size="sm" variant="outline" className="flex-1" onClick={() => openEdit(u)} data-testid={`emp-edit-${u.id}`}>
                    <PencilSimple size={12} className="mr-1" /> Edit
                  </Button>
                )}
                {u.id !== user.id && ["ceo", "admin"].includes(user.role) && (
                  <Button size="sm" variant="ghost" className="flex-1 text-red-500 hover:text-red-700" onClick={() => del(u.id)} data-testid={`emp-del-${u.id}`}>
                    <Trash size={12} className="mr-1" /> Remove
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function EmpForm({ employee, managers, role, onClose }) {
  const isEdit = Boolean(employee);
  const allowedRoles = role === "ceo" ? ["admin", "sales_manager", "salesperson"] :
                       role === "admin" ? ["sales_manager", "salesperson"] :
                       role === "sales_manager" ? ["salesperson"] : [];

  const [form, setForm] = useState({
    email: employee?.email || "",
    password: "",
    name: employee?.name || "",
    role: employee?.role || allowedRoles[0] || "salesperson",
    designation: employee?.designation || "",
    phone: employee?.phone || "",
    area: employee?.area || "",
    target: employee?.target ?? 0,
    reporting_manager_id: employee?.reporting_manager_id || "",
    photo_url: employee?.photo_url || "",
  });
  const [busy, setBusy] = useState(false);

  const canChangeRole = !isEdit || (employee && allowedRoles.includes(employee.role) || allowedRoles.includes(form.role));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      if (isEdit) {
        const payload = {
          name: form.name,
          designation: form.designation,
          phone: form.phone,
          area: form.area,
          target: Number(form.target) || 0,
          photo_url: form.photo_url,
          reporting_manager_id: form.reporting_manager_id || null,
        };
        if (canChangeRole && allowedRoles.includes(form.role)) payload.role = form.role;
        if (form.password.trim()) payload.password = form.password;
        await api.patch(`/users/${employee.id}`, payload);
        toast.success("Employee updated");
      } else {
        const payload = { ...form, target: Number(form.target) || 0 };
        if (!payload.reporting_manager_id) delete payload.reporting_manager_id;
        await api.post("/users", payload);
        toast.success("Employee added");
      }
      onClose();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-3 mt-4">
      <SheetHeader>
        <SheetTitle className="font-heading">{isEdit ? "Edit employee" : "New employee"}</SheetTitle>
      </SheetHeader>
      <div className="grid grid-cols-2 gap-3">
        <div><Label>Name</Label><Input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="emp-name-input" /></div>
        <div>
          <Label>Role</Label>
          <Select
            value={form.role}
            onValueChange={(v) => setForm({ ...form, role: v })}
            disabled={isEdit && !canChangeRole}
          >
            <SelectTrigger data-testid="emp-role-select"><SelectValue /></SelectTrigger>
            <SelectContent>
              {(isEdit ? [form.role, ...allowedRoles.filter((r) => r !== form.role)] : allowedRoles)
                .filter((r, i, arr) => arr.indexOf(r) === i)
                .map((r) => <SelectItem key={r} value={r}>{ROLE_LABEL[r]}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="col-span-2">
          <Label>Email</Label>
          <Input type="email" required={!isEdit} disabled={isEdit} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} data-testid="emp-email-input" />
        </div>
        <div className="col-span-2">
          <Label>{isEdit ? "New password (optional)" : "Password"}</Label>
          <Input type="password" required={!isEdit} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} data-testid="emp-password-input" />
        </div>
        <div><Label>Designation</Label><Input value={form.designation} onChange={(e) => setForm({ ...form, designation: e.target.value })} data-testid="emp-designation-input" /></div>
        <div><Label>Phone</Label><Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} data-testid="emp-phone-input" /></div>
        <div><Label>Area</Label><Input value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })} data-testid="emp-area-input" /></div>
        <div><Label>Monthly target (₹)</Label><Input type="number" value={form.target} onChange={(e) => setForm({ ...form, target: e.target.value })} data-testid="emp-target-input" /></div>
        <div className="col-span-2">
          <Label>Reporting manager</Label>
          <Select value={form.reporting_manager_id || "none"} onValueChange={(v) => setForm({ ...form, reporting_manager_id: v === "none" ? "" : v })}>
            <SelectTrigger data-testid="emp-manager-select"><SelectValue placeholder="Choose manager" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="none">— None —</SelectItem>
              {managers.filter((m) => !isEdit || m.id !== employee?.id).map((m) => (
                <SelectItem key={m.id} value={m.id}>{m.name} ({ROLE_LABEL[m.role]})</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="col-span-2"><Label>Photo URL (optional)</Label><Input value={form.photo_url} onChange={(e) => setForm({ ...form, photo_url: e.target.value })} /></div>
      </div>
      <Button type="submit" disabled={busy} className="w-full" data-testid="emp-save-btn">
        {busy ? "Saving…" : isEdit ? "Save changes" : "Add"}
      </Button>
    </form>
  );
}
