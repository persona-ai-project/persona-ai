"use client";

import { motion } from "framer-motion";
import { Mic } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function VoiceButton() {
  const [isRecording, setIsRecording] = useState(false);

  return (
    <Button
      type="button"
      variant="outline"
      size="icon"
      aria-label={isRecording ? "Stop recording" : "Start recording"}
      aria-pressed={isRecording}
      onClick={() => setIsRecording((prev) => !prev)}
      className={cn(
        "relative shrink-0 transition-colors",
        isRecording &&
          "border-destructive bg-destructive/20 text-destructive hover:bg-destructive/30 hover:text-destructive"
      )}
    >
      {isRecording && (
        <motion.span
          className="absolute inset-0 rounded-lg bg-destructive/30"
          animate={{ scale: [1, 1.15, 1], opacity: [0.6, 0.2, 0.6] }}
          transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
        />
      )}
      <Mic className={cn("relative z-10 size-4", isRecording && "text-destructive")} />
    </Button>
  );
}
