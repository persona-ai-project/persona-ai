"use client";

import { motion } from "framer-motion";
import { Bot, Pencil, RotateCcw } from "lucide-react";
import { useState } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

export type ChatMessage = {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: Date;
  chunks_used?: { text: string; score: number }[];
  message_id?: string;
};

interface ChatBubbleProps {
  message: ChatMessage;
  userId: string;
  onRegenerate?: (messageId: string) => void;
}

type Feedback = "up" | "down" | "rewrite" | null;

function formatTimestamp(date: Date): string {
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function MessageFeedback({ userId, message, onRegenerate }: { userId: string; message: ChatMessage; onRegenerate?: (id: string) => void }) {
  const [feedback, setFeedback] = useState<Feedback>(null);
  const [rewriteText, setRewriteText] = useState("");
  const [showRewrite, setShowRewrite] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const submitFeedback = async (kind: string, rewrite?: string) => {
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          user_id: userId,
          message: "",
          twin_response: message.content,
          kind,
          rewrite,
        }),
      });
      setSubmitted(true);
    } catch (e) {
      console.error("Feedback failed:", e);
    }
  };

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-0.5 px-1">
        <button
          type="button"
          aria-label="Helpful"
          onClick={() => { setFeedback("up"); submitFeedback("thumbs_up"); }}
          className={cn(
            "flex size-7 items-center justify-center rounded-md text-sm opacity-60 transition-all hover:opacity-100",
            feedback === "up" && "bg-primary/20 opacity-100 ring-1 ring-primary/40"
          )}
        >
          👍
        </button>
        <button
          type="button"
          aria-label="Not helpful"
          onClick={() => { setFeedback("down"); submitFeedback("thumbs_down"); }}
          className={cn(
            "flex size-7 items-center justify-center rounded-md text-sm opacity-60 transition-all hover:opacity-100",
            feedback === "down" && "bg-primary/20 opacity-100 ring-1 ring-primary/40"
          )}
        >
          👎
        </button>
        <button
          type="button"
          aria-label="Rewrite"
          onClick={() => setShowRewrite(!showRewrite)}
          className="flex size-7 items-center justify-center rounded-md text-sm opacity-60 transition-all hover:opacity-100"
        >
          <Pencil className="size-3.5" />
        </button>
        {message.message_id && onRegenerate && (
          <button
            type="button"
            aria-label="Regenerate"
            onClick={() => onRegenerate(message.message_id!)}
            className="flex size-7 items-center justify-center rounded-md text-sm opacity-60 transition-all hover:opacity-100"
          >
            <RotateCcw className="size-3.5" />
          </button>
        )}
      </div>
      {showRewrite && (
        <div className="flex gap-2 px-1">
          <input
            type="text"
            value={rewriteText}
            onChange={(e) => setRewriteText(e.target.value)}
            placeholder="Rewrite as you would say it..."
            className="flex-1 rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground"
            onKeyDown={(e) => {
              if (e.key === "Enter" && rewriteText.trim()) {
                submitFeedback("rewrite", rewriteText.trim());
                setShowRewrite(false);
                setRewriteText("");
              }
            }}
          />
          <button
            onClick={() => {
              if (rewriteText.trim()) {
                submitFeedback("rewrite", rewriteText.trim());
                setShowRewrite(false);
                setRewriteText("");
              }
            }}
            className="rounded-lg bg-primary px-3 py-1.5 text-xs text-primary-foreground hover:bg-primary/90"
          >
            Submit
          </button>
        </div>
      )}
      {submitted && feedback === "up" && <span className="px-1 text-xs text-green-500">Thanks!</span>}
      {submitted && feedback === "down" && <span className="px-1 text-xs text-muted-foreground">Noted</span>}
      {submitted && !feedback && <span className="px-1 text-xs text-green-500">Rewrite saved for DPO training</span>}
    </div>
  );
}

export function ChatBubble({ message, userId, onRegenerate }: ChatBubbleProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={cn(
        "flex w-full gap-2",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <Avatar size="sm" className="mt-1 shrink-0">
          <AvatarFallback className="bg-primary text-primary-foreground">
            <Bot className="size-3.5" />
          </AvatarFallback>
        </Avatar>
      )}

      <div
        className={cn(
          "flex max-w-[85%] flex-col gap-1 sm:max-w-[75%]",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed text-white whitespace-pre-wrap",
            isUser
              ? "rounded-br-md bg-primary"
              : "rounded-bl-md bg-surface"
          )}
        >
          {message.content}
        </div>
        <div className="flex items-center gap-2">
          <span className="px-1 text-xs text-muted-foreground">
            {formatTimestamp(message.timestamp)}
          </span>
          {!isUser && message.content.length > 0 && (
            <MessageFeedback userId={userId} message={message} onRegenerate={onRegenerate} />
          )}
        </div>
      </div>
    </motion.div>
  );
}
