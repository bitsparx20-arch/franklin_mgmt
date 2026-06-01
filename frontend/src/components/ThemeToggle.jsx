import React, { useEffect, useState } from "react";
import { Sun, Moon } from "@phosphor-icons/react";

export const ThemeToggle = () => {
  const [dark, setDark] = useState(() => localStorage.getItem("fw_theme") === "dark");
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("fw_theme", dark ? "dark" : "light");
  }, [dark]);
  return (
    <button
      onClick={() => setDark((v) => !v)}
      data-testid="theme-toggle-btn"
      className="h-9 w-9 inline-flex items-center justify-center rounded-md border border-border hover:bg-muted transition-colors"
      aria-label="Toggle theme"
    >
      {dark ? <Sun size={16} weight="bold" /> : <Moon size={16} weight="bold" />}
    </button>
  );
};
