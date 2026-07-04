"use client";

import { motion } from "framer-motion";
import { Bot } from "lucide-react";
import { useState } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

export type ChatMessage = {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: Date;
};

interface ChatBubbleProps {
  message: ChatMessage;
}

type Feedback = "up" | "down" | null;

function formatTimestamp(date: Date): string {
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function MessageFeedback() {
  const [feedback, setFeedback] = useState<Feedback>(null);

  return (
    <div className="flex items-center gap-0.5 px-1">
      <button
        type="button"
        aria-label="Helpful"
        onClick={() => setFeedback("up")}
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
        onClick={() => setFeedback("down")}
        className={cn(
          "flex size-7 items-center justify-center rounded-md text-sm opacity-60 transition-all hover:opacity-100",
          feedback === "down" && "bg-primary/20 opacity-100 ring-1 ring-primary/40"
        )}
      >
        👎
      </button>
    </div>
  );
}

export function ChatBubble({ message }: ChatBubbleProps) {
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
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed text-white",
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
          {!isUser && message.content.length > 0 && <MessageFeedback />}
        </div>
      </div>
    </motion.div>
  );
}
