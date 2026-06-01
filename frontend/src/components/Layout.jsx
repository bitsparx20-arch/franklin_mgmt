import React, { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  House, MapPin, Users, Phone, Kanban, Package, Receipt,
  ChartBar, UserCircle, Bell, FileText, SignOut, List as ListIcon,
} from "@phosphor-icons/react";
import { useAuth } from "../context/AuthContext";
import { ThemeToggle } from "./ThemeToggle";
import { ROLE_LABEL } from "../lib/format";
import api from "../lib/api";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "./ui/sheet";
import { Toaster } from "./ui/sonner";
import { AIChat } from "./AIChat";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "./ui/dropdown-menu";

const NAV = [
  { to: "/dashboard", icon: House, label: "Dashboard", roles: ["ceo", "admin", "sales_manager", "salesperson"] },
  { to: "/visits", icon: MapPin, label: "Visits", roles: ["ceo", "admin", "sales_manager", "salesperson"] },
  { to: "/pocs", icon: Phone, label: "POCs", roles: ["ceo", "admin", "sales_manager", "salesperson"] },
  { to: "/followups", icon: Bell, label: "Follow-ups", roles: ["ceo", "admin", "sales_manager", "salesperson"] },
  { to: "/pipeline", icon: Kanban, label: "Pipeline", roles: ["ceo", "admin", "sales_manager", "salesperson"] },
  { to: "/products", icon: Package, label: "Products", roles: ["ceo", "admin", "sales_manager", "salesperson"] },
  { to: "/bills", icon: Receipt, label: "Bills", roles: ["ceo", "admin", "sales_manager", "salesperson"] },
  { to: "/performance", icon: ChartBar, label: "Performance", roles: ["ceo", "admin", "sales_manager"] },
  { to: "/employees", icon: Users, label: "Employees", roles: ["ceo", "admin", "sales_manager"] },
  { to: "/reports", icon: FileText, label: "Reports", roles: ["ceo", "admin", "sales_manager", "salesperson"] },
];

const SidebarContent = ({ user, onNavigate, scope = "desktop" }) => (
  <div className="flex flex-col h-full">
    <div className="px-6 py-6 border-b border-border/60">
      <Link to="/dashboard" className="block" data-testid={`brand-link-${scope}`}>
        <div className="font-heading font-black text-lg tracking-tight leading-tight">
          FRANKLIN <span className="text-[hsl(var(--accent))]">/</span> WARDCORPP
        </div>
        <div className="overline mt-1">Sales Intelligence OS</div>
      </Link>
    </div>
    <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
      {NAV.filter((n) => n.roles.includes(user.role)).map((n) => (
        <NavLink
          key={n.to}
          to={n.to}
          onClick={onNavigate}
          data-testid={`nav-${n.label.toLowerCase().replace(/[^a-z]/g, "-")}-${scope}`}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
              isActive
                ? "bg-muted text-foreground font-semibold"
                : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
            }`
          }
        >
          <n.icon size={18} weight="regular" />
          {n.label}
        </NavLink>
      ))}
    </nav>
    <div className="p-4 border-t border-border/60">
      <div className="text-[10px] tracking-[0.2em] uppercase text-muted-foreground">v1.0 · SpringEdge SMS</div>
    </div>
  </div>
);

export const Layout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [notifs, setNotifs] = useState([]);

  const loadNotifs = async () => {
    try {
      const { data } = await api.get("/notifications");
      setNotifs(data);
    } catch {}
  };
  useEffect(() => {
    loadNotifs();
    const t = setInterval(loadNotifs, 30000);
    return () => clearInterval(t);
  }, []);

  const unread = notifs.filter((n) => !n.read).length;

  if (!user) return null;

  return (
    <div className="h-screen flex bg-background overflow-hidden">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-64 flex-col border-r border-border/60 bg-card">
        <SidebarContent user={user} />
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 border-b border-border/60 bg-background/80 backdrop-blur sticky top-0 z-30 flex items-center px-4 lg:px-8 gap-3">
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <button className="lg:hidden h-9 w-9 inline-flex items-center justify-center rounded-md border border-border" data-testid="mobile-menu-btn">
                <ListIcon size={18} weight="bold" />
              </button>
            </SheetTrigger>
            <SheetContent side="left" className="p-0 w-72">
              <span className="sr-only">
                <SheetTitle>Navigation</SheetTitle>
              </span>
              <SidebarContent user={user} onNavigate={() => setOpen(false)} scope="mobile" />
            </SheetContent>
          </Sheet>

          <div className="flex-1">
            <div className="font-heading font-bold tracking-tight text-sm">Welcome, {user.name.split(" ")[0]}</div>
            <div className="overline">{ROLE_LABEL[user.role]} · {user.area || "—"}</div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button data-testid="notifications-btn" className="relative h-9 w-9 inline-flex items-center justify-center rounded-md border border-border hover:bg-muted">
                <Bell size={16} weight="bold" />
                {unread > 0 && (
                  <span className="absolute -top-1 -right-1 bg-[hsl(var(--accent))] text-white text-[10px] font-bold rounded-full h-4 min-w-4 px-1 flex items-center justify-center font-mono">{unread}</span>
                )}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80">
              <DropdownMenuLabel className="font-heading">Notifications</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {notifs.length === 0 && <div className="px-3 py-6 text-center text-xs text-muted-foreground">No notifications</div>}
              {notifs.slice(0, 8).map((n) => (
                <DropdownMenuItem key={n.id} className="flex-col items-start gap-1 py-2">
                  <div className="font-semibold text-xs">{n.title}</div>
                  <div className="text-xs text-muted-foreground">{n.body}</div>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <ThemeToggle />

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button data-testid="profile-menu-btn" className="flex items-center gap-2 px-2 py-1.5 rounded-md border border-border hover:bg-muted">
                <UserCircle size={20} weight="regular" />
                <span className="hidden md:inline text-xs font-semibold">{user.name}</span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel className="font-mono text-[10px]">{user.email}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={async () => { await logout(); navigate("/login"); }} data-testid="logout-btn">
                <SignOut size={14} className="mr-2" /> Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        <main className="flex-1 p-4 md:p-6 lg:p-8 pb-24 md:pb-8">
          <Outlet context={{ refetchNotifs: loadNotifs }} />
        </main>
      </div>
      <Toaster richColors closeButton position="top-right" />
      <AIChat />
    </div>
  );
};
