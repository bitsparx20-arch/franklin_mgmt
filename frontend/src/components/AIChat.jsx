import React, { useEffect, useRef, useState } from "react";
import api from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "./ui/sheet";
import { ChatCircleDots, PaperPlaneTilt, Sparkle, X } from "@phosphor-icons/react";
import { toast } from "sonner";

const QUICK_PROMPTS = [
  "Summarize this month's pipeline health.",
  "Who are my top 3 performers and why?",
  "What deals should I focus on this week?",
  "Where are we losing revenue?",
  "Suggest 3 actions for tomorrow's standup.",
];

export const AIChat = () => {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!user || !["ceo", "admin", "sales_manager"].includes(user.role)) return null;

  const send = async (text) => {
    if (!text.trim() || busy) return;
    const userMsg = { role: "user", text };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setBusy(true);
    try {
      const { data } = await api.post("/ai/ask", { session_id: sessionId, message: text });
      setSessionId(data.session_id);
      setMessages((m) => [...m, { role: "assistant", text: data.reply }]);
    } catch (e) {
      const detail = e?.response?.data?.detail;
      const msg = typeof detail === "string" ? detail : "AI request failed";
      toast.error(msg.length > 120 ? msg.slice(0, 120) + "…" : msg);
      setMessages((m) => [...m, { role: "assistant", text: `_Error: ${typeof detail === "string" ? detail : "Could not reach the AI service."}_` }]);
    } finally { setBusy(false); }
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button
          data-testid="ai-chat-fab"
          className="fixed bottom-6 right-6 z-40 h-14 w-14 rounded-full bg-foreground text-background shadow-xl hover:scale-105 transition-transform flex items-center justify-center group"
          aria-label="Open AI chat"
        >
          <Sparkle size={22} weight="fill" className="text-[hsl(var(--accent))] group-hover:rotate-12 transition-transform" />
          <span className="absolute -top-1 -right-1 h-3 w-3 bg-[hsl(var(--accent))] rounded-full animate-pulse" />
        </button>
      </SheetTrigger>
      <SheetContent side="right" className="z-[100] w-full sm:max-w-md p-0 flex flex-col">
        <SheetHeader className="px-5 py-4 border-b border-border">
          <SheetTitle className="font-heading flex items-center gap-2">
            <Sparkle size={18} weight="fill" className="text-[hsl(var(--accent))]" />
            Franklin-AI Assistant
          </SheetTitle>
          <div className="text-[10px] tracking-[0.2em] uppercase text-muted-foreground">Live CRM context</div>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {messages.length === 0 && (
            <div>
              <p className="text-sm text-muted-foreground mb-3">Ask anything about your sales pipeline, performance, or revenue. I read your live CRM data.</p>
              <div className="space-y-1.5">
                {QUICK_PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => send(p)}
                    data-testid={`ai-prompt-${p.slice(0, 10)}`}
                    className="w-full text-left text-xs border border-border rounded-md px-3 py-2 hover:bg-muted hover:border-foreground/30 transition-colors"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[88%] rounded-lg px-3 py-2.5 text-sm ${
                m.role === "user"
                  ? "bg-foreground text-background"
                  : "bg-muted border border-border"
              }`} data-testid={`ai-msg-${m.role}-${i}`}>
                <Markdown text={m.text} />
              </div>
            </div>
          ))}
          {busy && (
            <div className="flex justify-start">
              <div className="bg-muted border border-border rounded-lg px-3 py-2.5 text-sm flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-foreground/60 animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="h-2 w-2 rounded-full bg-foreground/60 animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="h-2 w-2 rounded-full bg-foreground/60 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <form
          onSubmit={(e) => { e.preventDefault(); send(input); }}
          className="border-t border-border p-3 flex gap-2"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about pipeline, revenue, performance…"
            disabled={busy}
            data-testid="ai-chat-input"
            className="font-sans"
          />
          <Button type="submit" disabled={busy || !input.trim()} data-testid="ai-chat-send-btn">
            <PaperPlaneTilt size={16} weight="bold" />
          </Button>
        </form>
      </SheetContent>
    </Sheet>
  );
};

// Lightweight markdown renderer (headings, bold, lists, code)
function Markdown({ text }) {
  const html = formatMarkdown(text);
  return <div className="prose-sm space-y-1.5" dangerouslySetInnerHTML={{ __html: html }} />;
}

function formatMarkdown(t) {
  if (!t) return "";
  // Escape basic HTML
  let s = t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  // Headings
  s = s.replace(/^### (.*)$/gm, '<div class="font-heading font-bold text-sm mt-2">$1</div>');
  s = s.replace(/^## (.*)$/gm, '<div class="font-heading font-bold text-base mt-2">$1</div>');
  // Bold
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Italic
  s = s.replace(/(^|[^*])\*([^*]+)\*/g, '$1<em>$2</em>');
  // Bullets
  s = s.replace(/^[-•] (.+)$/gm, '<div class="flex gap-1.5"><span class="text-[hsl(var(--accent))]">›</span><span>$1</span></div>');
  // Numbered
  s = s.replace(/^\d+\.\s+(.+)$/gm, '<div class="flex gap-1.5"><span class="font-mono text-[hsl(var(--accent))]">•</span><span>$1</span></div>');
  // Inline code
  s = s.replace(/`([^`]+)`/g, '<code class="font-mono text-[11px] bg-background/60 px-1 rounded">$1</code>');
  // Line breaks
  s = s.replace(/\n\n/g, '<br/>');
  s = s.replace(/\n/g, ' ');
  return s;
}
