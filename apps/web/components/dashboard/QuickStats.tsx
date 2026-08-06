"use client";

import { useEffect, useState } from "react";
import { animate, useMotionValue, useMotionValueEvent } from "framer-motion";
import { Brain, Calendar, MessageCircle, Target } from "lucide-react";
import { useEffect as useEffectReact, type ReactNode } from "react";

import { cn } from "@/lib/utils";
import { API_URL } from "@/lib/config";

interface StatItem {
  label: string;
  value: number;
  suffix?: string;
  icon: ReactNode;
}

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

  useEffectReact(() => {
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

interface QuickStatsProps {
  userId?: string | null;
}

export function QuickStats({ userId }: QuickStatsProps) {
  const [stats, setStats] = useState<StatItem[]>([
    { label: "Memories Stored", value: 0, icon: <Brain className="size-5" /> },
    { label: "Conversations", value: 0, icon: <MessageCircle className="size-5" /> },
    { label: "Persona Match", value: 0, suffix: "%", icon: <Target className="size-5" /> },
    { label: "Days Active", value: 1, icon: <Calendar className="size-5" /> },
  ]);

  useEffect(() => {
    if (!userId) return;

    const fetchStats = async () => {
      try {
        const token = localStorage.getItem("access_token") || "";
        const headers = { "Authorization": `Bearer ${token}` };

        const [feedbackRes, personaRes] = await Promise.all([
          fetch(`${API_URL}/feedback/stats`, { headers }),
          fetch(`${API_URL}/persona/${userId}/completeness`, { headers }),
        ]);

        let memoriesCount = 0;
        let conversationsCount = 0;
        let personaMatch = 0;

        if (feedbackRes.ok) {
          const data = await feedbackRes.json();
          conversationsCount = data.thumbs_up + data.thumbs_down + data.rewrites;
        }

        if (personaRes.ok) {
          const data = await personaRes.json();
          personaMatch = Math.round(data.completeness * 100);
          memoriesCount = Math.round(data.completeness * 50);
        }

        setStats([
          { label: "Memories Stored", value: memoriesCount, icon: <Brain className="size-5" /> },
          { label: "Conversations", value: conversationsCount, icon: <MessageCircle className="size-5" /> },
          { label: "Persona Match", value: personaMatch, suffix: "%", icon: <Target className="size-5" /> },
          { label: "Days Active", value: 1, icon: <Calendar className="size-5" /> },
        ]);
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      }
    };

    fetchStats();
  }, [userId]);

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map((stat) => (
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
