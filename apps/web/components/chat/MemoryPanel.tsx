"use client";

import { motion } from "framer-motion";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface Memory {
  id: string;
  text: string;
  relevance: string;
}

interface MemoryPanelProps {
  className?: string;
  memories?: Memory[];
}

const DEFAULT_MEMORIES: Memory[] = [
  {
    id: "1",
    text: "Start chatting to build your AI twin's memory...",
    relevance: "system",
  },
];

export function MemoryPanel({ className, memories = DEFAULT_MEMORIES }: MemoryPanelProps) {
  return (
    <aside
      className={cn(
        "flex h-full flex-col border-l border-border bg-background",
        className
      )}
    >
      <div className="shrink-0 border-b border-border px-4 py-4">
        <h2 className="text-sm font-semibold text-foreground">
          What I Remember
        </h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Relevant context from your profile
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="flex flex-col gap-3">
          {memories.map((memory, index) => (
            <motion.div
              key={memory.id}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.08 }}
              className="rounded-lg border border-border bg-surface p-3 pl-4"
              style={{ borderLeftWidth: "3px", borderLeftColor: "#8b5cf6" }}
            >
              <p className="text-xs leading-relaxed text-muted-foreground">
                {memory.text}
              </p>
              <Badge
                variant="default"
                className="mt-2 bg-primary/20 text-primary hover:bg-primary/20"
              >
                {memory.relevance}
              </Badge>
            </motion.div>
          ))}
        </div>
      </div>
    </aside>
  );
}
