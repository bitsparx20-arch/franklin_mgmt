export const formatINR = (n) => {
  if (n == null || isNaN(n)) return "₹0";
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);
};

export const formatDate = (d) => {
  if (!d) return "—";
  try {
    return new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  } catch { return "—"; }
};

export const formatDateTime = (d) => {
  if (!d) return "—";
  try {
    return new Date(d).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
  } catch { return "—"; }
};

export const daysUntil = (d) => {
  if (!d) return null;
  const diff = (new Date(d).getTime() - Date.now()) / 86400000;
  return Math.ceil(diff);
};

export const followUpColor = (d) => {
  const days = daysUntil(d);
  if (days == null) return "muted";
  if (days < 0) return "red";
  if (days === 0) return "amber";
  return "green";
};

export const conversionColor = (rate) => {
  if (rate >= 80) return "text-emerald-600 dark:text-emerald-400";
  if (rate >= 50) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
};

export const stageMeta = {
  COLD_LEAD: { label: "COLD LEAD", color: "bg-zinc-400", text: "text-zinc-700 dark:text-zinc-200" },
  CONTACTED: { label: "CONTACTED", color: "bg-blue-500", text: "text-blue-700 dark:text-blue-300" },
  INTERESTED: { label: "INTERESTED", color: "bg-amber-500", text: "text-amber-700 dark:text-amber-300" },
  NEGOTIATION: { label: "NEGOTIATION", color: "bg-orange-500", text: "text-orange-700 dark:text-orange-300" },
  WON: { label: "WON ✓", color: "bg-emerald-600", text: "text-emerald-700 dark:text-emerald-300" },
  LOST: { label: "LOST ✕", color: "bg-red-600", text: "text-red-700 dark:text-red-300" },
};

export const ROLE_LABEL = {
  ceo: "CEO", admin: "Admin", sales_manager: "Sales Manager", salesperson: "Salesperson",
};
