"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Send, User } from "lucide-react";

import { API_URL } from "@/lib/config";

type Message = {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: Date;
};

function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className="flex gap-2"
    >
      <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
        <Bot className="size-4" />
      </div>
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-md bg-surface px-4 py-3">
        <span className="size-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:-0.3s]" />
        <span className="size-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:-0.15s]" />
        <span className="size-2 animate-bounce rounded-full bg-muted-foreground/40" />
      </div>
    </motion.div>
  );
}

export default function PublicTwinPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [twinName, setTwinName] = useState("AI Twin");
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    const loadTwin = async () => {
      try {
        const res = await fetch(`${API_URL}/persona/${slug}`);
        if (res.ok) {
          const data = await res.json();
          if (data.name) setTwinName(data.name);
        }
      } catch {
        // Use default name
      }
    };
    loadTwin();
  }, [slug]);

  const streamResponse = useCallback(async (userMessage: string) => {
    const aiId = `ai-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: aiId, role: "ai", content: "", timestamp: new Date() },
    ]);

    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: slug, message: userMessage }),
      });

      if (!response.ok) throw new Error("Failed to get response");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      let currentContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "token" && data.content) {
                currentContent += data.content;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === aiId ? { ...m, content: currentContent } : m
                  )
                );
              }
              if (data.type === "done") break;
            } catch {}
          }
        }
      }
    } catch (e) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiId
            ? { ...m, content: "Sorry, I encountered an error. Please try again." }
            : m
        )
      );
    }
  }, [slug]);

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isTyping || isStreaming) return;

    setMessages((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: "user", content: trimmed, timestamp: new Date() },
    ]);
    setInput("");
    setIsTyping(true);
    setIsStreaming(true);

    await new Promise((r) => setTimeout(r, 300));
    setIsTyping(false);
    await streamResponse(trimmed);
    setIsStreaming(false);
  }, [input, isTyping, isStreaming, streamResponse]);

  return (
    <div className="flex h-dvh flex-col bg-background">
      <header className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <h1 className="text-lg font-semibold text-primary">PersonaAI</h1>
          <span className="text-sm text-muted-foreground">Chatting with {twinName}</span>
        </div>
      </header>

      <main className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
          <div className="mx-auto flex max-w-3xl flex-col gap-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="mb-4 flex size-16 items-center justify-center rounded-full bg-primary/10">
                  <Bot className="size-8 text-primary" />
                </div>
                <h2 className="mb-2 text-xl font-semibold text-foreground">
                  Chat with {twinName}
                </h2>
                <p className="max-w-sm text-sm text-muted-foreground">
                  This is a public AI twin. Start a conversation to learn about this person.
                </p>
              </div>
            )}

            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex w-full gap-2 ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {message.role === "ai" && (
                  <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground mt-1">
                    <Bot className="size-4" />
                  </div>
                )}
                <div className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed text-white whitespace-pre-wrap ${
                  message.role === "user"
                    ? "rounded-br-md bg-primary"
                    : "rounded-bl-md bg-surface"
                }`}>
                  {message.content || "..."}
                </div>
              </motion.div>
            ))}

            <AnimatePresence>
              {isTyping && <TypingIndicator />}
            </AnimatePresence>

            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="shrink-0 border-t border-border bg-background p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="mx-auto flex max-w-3xl gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Ask ${twinName} something...`}
              className="flex-1 rounded-xl border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              disabled={isStreaming}
            />
            <button
              type="submit"
              disabled={!input.trim() || isStreaming}
              className="flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              <Send className="size-5" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
