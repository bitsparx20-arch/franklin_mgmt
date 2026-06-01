import React, { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { toast } from "sonner";
import { Toaster } from "../components/ui/sonner";
import { ArrowRight, Lightning } from "@phosphor-icons/react";

const DEMO = [
  { role: "CEO", email: "ceo@franklinwardcorpp.com", pw: "ceo12345" },
  { role: "Admin", email: "admin@franklinwardcorpp.com", pw: "admin123" },
  { role: "Manager", email: "manager@franklinwardcorpp.com", pw: "manager123" },
  { role: "Sales", email: "sales1@franklinwardcorpp.com", pw: "sales123" },
];

export default function Login() {
  const { user, login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/dashboard" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await login(email, password);
      toast.success("Welcome back");
      nav("/dashboard");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Login failed");
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 overflow-hidden grid lg:grid-cols-5 bg-background">
      {/* Left: Hero */}
      <div className="hidden lg:flex lg:col-span-3 relative bg-zinc-950 text-white overflow-hidden grain h-full">
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "url('https://images.pexels.com/photos/7230895/pexels-photo-7230895.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940')",
            backgroundSize: "cover", backgroundPosition: "center",
            filter: "grayscale(80%)",
          }}
        />
        <div className="relative z-10 p-12 xl:p-16 flex flex-col justify-between w-full">
          <div>
            <div className="inline-flex items-center gap-2 border border-white/20 rounded-full px-3 py-1 text-[10px] tracking-[0.2em] uppercase">
              <Lightning weight="fill" size={12} className="text-[hsl(var(--accent))]" /> Sales Intelligence OS
            </div>
            <h1 className="mt-8 font-heading font-black text-5xl xl:text-6xl leading-[0.95] tracking-tighter">
              FRANKLIN<br/>
              <span className="text-[hsl(var(--accent))]">WARDCORPP</span><br/>
              CRM
            </h1>
            <p className="mt-6 max-w-md text-zinc-300 text-sm leading-relaxed">
              Field tracking · POC follow-ups · Kanban pipeline · GST invoicing · Performance analytics.
              One unified workspace for the entire revenue team.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-6 max-w-xl">
            <Stat label="MODULES" value="09" />
            <Stat label="ROLES" value="04" />
            <Stat label="LIVE GPS" value="ON" />
          </div>
        </div>
      </div>

      {/* Right: Form */}
      <div className="lg:col-span-2 flex items-center justify-center p-6 lg:p-12 h-full overflow-y-auto">
        <div className="w-full max-w-sm">
          <div className="lg:hidden mb-8">
            <div className="font-heading font-black text-2xl tracking-tighter">
              FRANKLIN<span className="text-[hsl(var(--accent))]">/</span>WARDCORPP
            </div>
            <div className="overline mt-1">CRM</div>
          </div>
          <div className="overline">Sign in</div>
          <h2 className="mt-2 font-heading font-bold text-3xl tracking-tight">Welcome back.</h2>
          <p className="text-sm text-muted-foreground mt-1">Pick a demo role below or enter your credentials.</p>

          <form onSubmit={submit} className="mt-8 space-y-4">
            <div>
              <Label htmlFor="email" className="text-xs uppercase tracking-wider">Email</Label>
              <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="mt-1.5 font-mono" data-testid="login-email-input" />
            </div>
            <div>
              <Label htmlFor="pw" className="text-xs uppercase tracking-wider">Password</Label>
              <Input id="pw" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="mt-1.5 font-mono" data-testid="login-password-input" />
            </div>
            <Button type="submit" disabled={busy} className="w-full rounded-md h-11 font-semibold tracking-wide" data-testid="login-submit-btn">
              {busy ? "Signing in…" : "Sign in"}
              <ArrowRight size={16} className="ml-2" weight="bold" />
            </Button>
          </form>

          <div className="mt-8 border-t border-border pt-6">
            <div className="overline mb-3">Demo accounts</div>
            <div className="grid grid-cols-2 gap-2">
              {DEMO.map((d) => (
                <button
                  key={d.email}
                  type="button"
                  data-testid={`demo-${d.role.toLowerCase()}-btn`}
                  onClick={() => { setEmail(d.email); setPassword(d.pw); }}
                  className="text-left border border-border rounded-md px-3 py-2 hover:bg-muted transition-colors"
                >
                  <div className="text-xs font-semibold">{d.role}</div>
                  <div className="text-[10px] font-mono text-muted-foreground truncate">{d.email}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
      <Toaster richColors position="top-right" />
    </div>
  );
}

const Stat = ({ label, value }) => (
  <div>
    <div className="font-mono text-3xl font-bold">{value}</div>
    <div className="text-[10px] tracking-[0.2em] uppercase text-zinc-400 mt-1">{label}</div>
  </div>
);
