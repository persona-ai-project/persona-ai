"use client";

import { animate, useMotionValue, useMotionValueEvent } from "framer-motion";
import { Brain, Calendar, MessageCircle, Target } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

interface StatItem {
  label: string;
  value: number;
  suffix?: string;
  icon: ReactNode;
}

const STATS: StatItem[] = [
  {
    label: "Memories Stored",
    value: 247,
    icon: <Brain className="size-5" />,
  },
  {
    label: "Conversations",
    value: 12,
    icon: <MessageCircle className="size-5" />,
  },
  {
    label: "Persona Match",
    value: 94,
    suffix: "%",
    icon: <Target className="size-5" />,
  },
  {
    label: "Days Active",
    value: 18,
    icon: <Calendar className="size-5" />,
  },
];

function AnimatedStatValue({
  value,
  suffix = "",
}: {
  value: number;
  suffix?: string;
}) {
  const motionValue = useMotionValue(0);
  const [display, setDisplay] = useState(0);

  useMotionValueEvent(motionValue, "change", (latest) => {
    setDisplay(Math.round(latest));
  });

  useEffect(() => {
    const controls = animate(motionValue, value, {
      duration: 1.5,
      ease: "easeOut",
    });
    return controls.stop;
  }, [motionValue, value]);

  return (
    <span>
      {display}
      {suffix}
    </span>
  );
}

export function QuickStats() {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {STATS.map((stat) => (
        <div
          key={stat.label}
          className={cn(
            "flex flex-col gap-3 rounded-xl bg-surface p-4 ring-1 ring-foreground/10",
            "transition-colors hover:ring-primary/30"
          )}
        >
          <div className="text-primary">{stat.icon}</div>
          <div className="text-2xl font-bold text-white">
            <AnimatedStatValue value={stat.value} suffix={stat.suffix} />
          </div>
          <p className="text-sm text-muted-foreground">{stat.label}</p>
        </div>
      ))}
    </div>
  );
}
