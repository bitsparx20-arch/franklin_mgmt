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
      if (!err?.response) {
        toast.error("Cannot reach API — is the backend running on port 8000?");
        return;
      }
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-shell relative flex h-dvh max-h-dvh w-full flex-col overflow-hidden bg-background">
      {/* Hero — full-height left half on desktop */}
      <section
        className="login-hero-panel relative hidden overflow-hidden bg-zinc-950 text-white grain lg:fixed lg:inset-y-0 lg:left-0 lg:z-0 lg:flex lg:h-dvh lg:w-1/2 lg:flex-col"
        aria-hidden="true"
      >
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "url('https://images.pexels.com/photos/7230895/pexels-photo-7230895.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940')",
            backgroundSize: "cover",
            backgroundPosition: "center",
            filter: "grayscale(80%)",
          }}
        />
        <div className="relative z-10 flex h-full min-h-0 flex-col justify-between p-6 xl:p-10 2xl:p-14">
          <div className="min-h-0">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/20 px-3 py-1 text-[10px] uppercase tracking-[0.2em]">
              <Lightning weight="fill" size={12} className="text-[hsl(var(--accent))]" />
              Sales Intelligence OS
            </div>
            <h1 className="login-hero-title mt-4 font-heading font-black leading-[0.95] tracking-tighter xl:mt-6">
              FRANKLIN
              <br />
              <span className="text-[hsl(var(--accent))]">WARDCORPP</span>
              <br />
              CRM
            </h1>
            <p className="login-hero-desc mt-4 max-w-md text-sm leading-relaxed text-zinc-300">
              Field tracking · POC follow-ups · Kanban pipeline · GST invoicing · Performance analytics.
              One unified workspace for the entire revenue team.
            </p>
          </div>
          <div className="login-hero-stats mt-6 grid shrink-0 grid-cols-3 gap-4 sm:gap-6">
            <Stat label="MODULES" value="09" />
            <Stat label="ROLES" value="04" />
            <Stat label="LIVE GPS" value="ON" />
          </div>
        </div>
      </section>

      {/* Sign-in panel — all breakpoints */}
      <section className="relative z-10 flex min-h-dvh flex-1 flex-col bg-background lg:ml-[50%] lg:w-1/2">
        <header className="shrink-0 border-b border-border px-4 py-3 sm:px-6 lg:hidden">
          <div className="font-heading text-xl font-black tracking-tighter sm:text-2xl">
            FRANKLIN<span className="text-[hsl(var(--accent))]">/</span>WARDCORPP
          </div>
          <div className="overline mt-0.5">CRM</div>
        </header>

        <div className="login-form-scroll flex min-h-0 flex-1 flex-col overflow-y-auto overscroll-contain">
          <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center px-4 py-5 sm:px-6 sm:py-8 lg:px-10 lg:py-6 xl:px-12">
            <div className="overline">Sign in</div>
            <h2 className="login-welcome mt-1 font-heading font-bold tracking-tight">Welcome back.</h2>
            <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
              Pick a demo role below or enter your credentials.
            </p>

            <form onSubmit={submit} className="login-form mt-5 space-y-3 sm:mt-6 sm:space-y-4">
              <div>
                <Label htmlFor="email" className="text-xs uppercase tracking-wider">
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-1 h-10 font-mono sm:h-11"
                  data-testid="login-email-input"
                />
              </div>
              <div>
                <Label htmlFor="pw" className="text-xs uppercase tracking-wider">
                  Password
                </Label>
                <Input
                  id="pw"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="mt-1 h-10 font-mono sm:h-11"
                  data-testid="login-password-input"
                />
              </div>
              <Button
                type="submit"
                disabled={busy}
                className="h-10 w-full rounded-md text-sm font-semibold tracking-wide sm:h-11"
                data-testid="login-submit-btn"
              >
                {busy ? "Signing in…" : "Sign in"}
                <ArrowRight size={16} className="ml-2" weight="bold" />
              </Button>
            </form>

            <div className="login-demo mt-5 border-t border-border pt-5 sm:mt-6 sm:pt-6">
              <div className="overline mb-2 sm:mb-3">Demo accounts</div>
              <div className="grid grid-cols-1 gap-2 min-[400px]:grid-cols-2">
                {DEMO.map((d) => (
                  <button
                    key={d.email}
                    type="button"
                    data-testid={`demo-${d.role.toLowerCase()}-btn`}
                    onClick={() => {
                      setEmail(d.email);
                      setPassword(d.pw);
                    }}
                    className="rounded-md border border-border px-3 py-2 text-left transition-colors hover:bg-muted sm:py-2.5"
                  >
                    <div className="text-xs font-semibold">{d.role}</div>
                    <div className="truncate font-mono text-[10px] text-muted-foreground">{d.email}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <Toaster richColors position="top-right" />
    </div>
  );
}

const Stat = ({ label, value }) => (
  <div>
    <div className="login-stat-value font-mono font-bold">{value}</div>
    <div className="mt-0.5 text-[10px] uppercase tracking-[0.2em] text-zinc-400">{label}</div>
  </div>
);
