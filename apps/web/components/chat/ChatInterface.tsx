"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Brain, Send } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { ChatBubble, type ChatMessage } from "@/components/chat/ChatBubble";
import { MemoryPanel } from "@/components/chat/MemoryPanel";
import { VoiceButton } from "@/components/chat/VoiceButton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const MOCK_RESPONSE =
  "That's a great question! Based on what I know about you, I can provide personalized insights that help you grow both professionally and personally.";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/chat", label: "Chat" },
  { href: "/onboarding", label: "Onboarding" },
] as const;

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: "init-1",
    role: "ai",
    content:
      "Hello! I'm your PersonaAI twin. I've learned from your onboarding. Ask me anything.",
    timestamp: new Date("2026-06-06T10:00:00"),
  },
  {
    id: "init-2",
    role: "user",
    content: "What are my top strengths?",
    timestamp: new Date("2026-06-06T10:01:00"),
  },
  {
    id: "init-3",
    role: "ai",
    content:
      "Based on your profile, your top strengths are analytical thinking, goal orientation, and technical expertise.",
    timestamp: new Date("2026-06-06T10:01:30"),
  },
];

function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      className="flex items-center gap-2"
    >
      <Avatar size="sm" className="shrink-0">
        <AvatarFallback className="bg-primary text-primary-foreground">
          <span className="text-[10px] font-semibold">AI</span>
        </AvatarFallback>
      </Avatar>
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-md bg-surface px-4 py-3">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="size-2 rounded-full bg-primary"
            animate={{ y: [0, -6, 0] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              delay: i * 0.15,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
    </motion.div>
  );
}

export function ChatInterface() {
  const pathname = usePathname();
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showMemoryPanel, setShowMemoryPanel] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  const streamResponse = useCallback(async () => {
    const words = MOCK_RESPONSE.split(" ");
    const aiId = `ai-${Date.now()}`;
    const timestamp = new Date();

    setMessages((prev) => [
      ...prev,
      { id: aiId, role: "ai", content: "", timestamp },
    ]);

    let currentContent = "";
    for (let i = 0; i < words.length; i++) {
      currentContent += (i === 0 ? "" : " ") + words[i];
      const content = currentContent;
      setMessages((prev) =>
        prev.map((m) => (m.id === aiId ? { ...m, content } : m))
      );
      await new Promise((resolve) => setTimeout(resolve, 30));
    }

    setIsStreaming(false);
  }, []);

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isTyping || isStreaming) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);
    setIsStreaming(true);

    await new Promise((resolve) => setTimeout(resolve, 1000));

    setIsTyping(false);
    await streamResponse();
  }, [input, isTyping, isStreaming, streamResponse]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <div className="flex h-dvh flex-col bg-background">
      {/* Navbar */}
      <header className="sticky top-0 z-10 shrink-0 border-b border-border bg-background/95 backdrop-blur-sm">
        <div className="relative mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <Link
            href="/"
            className="text-lg font-semibold tracking-tight text-primary sm:text-xl"
          >
            PersonaAI
          </Link>

          <h1 className="absolute left-1/2 hidden -translate-x-1/2 text-sm font-medium text-foreground sm:block sm:text-base">
            Faizan&apos;s Twin
          </h1>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              className="lg:hidden"
              aria-label={showMemoryPanel ? "Hide memory panel" : "Show memory panel"}
              onClick={() => setShowMemoryPanel((prev) => !prev)}
            >
              <Brain className="size-4 text-primary" />
            </Button>
            <Avatar size="sm">
              <AvatarFallback className="bg-primary text-xs font-semibold text-primary-foreground">
                F
              </AvatarFallback>
            </Avatar>
          </div>
        </div>

        <nav className="mx-auto flex max-w-7xl items-center justify-center gap-1 border-t border-border px-4 py-2 sm:gap-6 sm:px-6">
          {NAV_LINKS.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:bg-white/5 hover:text-white"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </header>

      {/* Main content */}
      <div className="relative flex min-h-0 flex-1">
        {/* Chat area — 75% */}
        <div className="flex min-w-0 flex-[3] flex-col">
          <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
            <div className="mx-auto flex max-w-3xl flex-col gap-4">
              {messages.map((message) => (
                <ChatBubble key={message.id} message={message} />
              ))}

              <AnimatePresence>
                {isTyping && <TypingIndicator />}
              </AnimatePresence>

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input bar */}
          <div className="shrink-0 border-t border-border bg-background px-4 py-3 sm:px-6">
            <div className="mx-auto flex w-full max-w-3xl items-center gap-1.5 sm:gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask your twin anything..."
                disabled={isTyping || isStreaming}
                className="h-10 flex-1 bg-surface"
              />
              <VoiceButton />
              <Button
                type="button"
                size="icon"
                onClick={() => void handleSend()}
                disabled={!input.trim() || isTyping || isStreaming}
                aria-label="Send message"
              >
                <Send className="size-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Memory panel — 25% (desktop) */}
        <div className="hidden min-w-0 flex-1 lg:flex">
          <MemoryPanel className="w-full" />
        </div>

        {/* Memory panel — mobile overlay */}
        <AnimatePresence>
          {showMemoryPanel && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 z-20 bg-black/50 lg:hidden"
                onClick={() => setShowMemoryPanel(false)}
              />
              <motion.div
                initial={{ x: "100%" }}
                animate={{ x: 0 }}
                exit={{ x: "100%" }}
                transition={{ type: "spring", damping: 28, stiffness: 300 }}
                className="absolute inset-y-0 right-0 z-30 w-[85%] max-w-sm lg:hidden"
              >
                <MemoryPanel className="h-full shadow-xl" />
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
