"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Send } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { ChatBubble, type ChatMessage } from "@/components/chat/ChatBubble";
import { MemoryPanel } from "@/components/chat/MemoryPanel";
import { VoiceButton } from "@/components/chat/VoiceButton";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { NavBar } from "@/components/layout/NavBar";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { API_URL } from "@/lib/config";

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: "init-1",
    role: "ai",
    content:
      "Hello! I'm your PersonaAI twin. I've learned from your onboarding. Ask me anything.",
    timestamp: new Date(),
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
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showMemoryPanel, setShowMemoryPanel] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [memories, setMemories] = useState<Array<{id: string; text: string; relevance: string}>>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get user ID from localStorage on mount
  useEffect(() => {
    const storedUserId = localStorage.getItem("user_id");
    if (storedUserId) {
      setUserId(storedUserId);
    }
  }, []);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  const streamResponse = useCallback(async (userMessage: string) => {
    if (!userId) return;

    const aiId = `ai-${Date.now()}`;
    const timestamp = new Date();

    setMessages((prev) => [
      ...prev,
      { id: aiId, role: "ai", content: "", timestamp },
    ]);

    try {
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${localStorage.getItem("access_token") || ""}`,
        },
        body: JSON.stringify({
          user_id: userId,
          message: userMessage,
        }),
      });

      if (!response.ok) {
        throw new Error("Chat request failed");
      }

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
              if (data.type === "chunks" && data.chunks) {
                setMemories(data.chunks.map((c: { text: string; score: number }, i: number) => ({
                  id: `rag-${i}`,
                  text: c.text,
                  relevance: `score: ${c.score}`,
                })));
              }
              if (data.type === "done") break;
              if (data.type === "error") {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === aiId
                      ? { ...m, content: `Error: ${data.content}` }
                      : m
                  )
                );
              }
            } catch {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (error) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiId
            ? { ...m, content: "Sorry, I encountered an error. Please try again." }
            : m
        )
      );
    }

    setIsStreaming(false);
  }, [userId]);

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

    setMemories([]);

    await new Promise((resolve) => setTimeout(resolve, 500));
    setIsTyping(false);
    await streamResponse(trimmed);
  }, [input, isTyping, isStreaming, streamResponse]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <AuthGuard>
    <div className="flex h-dvh flex-col bg-background">
      {/* Navbar */}
      <NavBar title="Your AI Twin" initials="U" />

      {/* Main content */}
      <div className="relative flex min-h-0 flex-1">
        {/* Chat area — 75% */}
        <div className="flex min-w-0 flex-[3] flex-col">
          <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
            <div className="mx-auto flex max-w-3xl flex-col gap-4">
              {messages.map((message) => (
                <ChatBubble key={message.id} message={message} userId={userId} />
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
              <VoiceButton onTranscription={(text) => setInput((prev) => prev + text)} />
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
          <MemoryPanel className="w-full" memories={memories} />
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
                <MemoryPanel className="h-full shadow-xl" memories={memories} />
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>
    </div>
    </AuthGuard>
  );
}
