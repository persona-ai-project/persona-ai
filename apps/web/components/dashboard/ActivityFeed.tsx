"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface ActivityItem {
  icon: string;
  title: string;
  time: string;
}

interface ActivityFeedProps {
  userId?: string | null;
}

const DEFAULT_ACTIVITIES: ActivityItem[] = [
  { icon: "\ud83d\udcac", title: "Welcome to PersonaAI!", time: "Just now" },
  { icon: "\ud83e\udde0", title: "Start chatting to build your AI twin", time: "Just now" },
  { icon: "\u2705", title: "Complete onboarding to unlock features", time: "Just now" },
];

export function ActivityFeed({ userId }: ActivityFeedProps) {
  const [activities, setActivities] = useState<ActivityItem[]>(DEFAULT_ACTIVITIES);

  useEffect(() => {
    if (!userId) return;

    const fetchActivities = async () => {
      try {
        const token = localStorage.getItem("access_token") || "";
        const headers = { "Authorization": `Bearer ${token}` };

        const [feedbackRes, ingestRes] = await Promise.all([
          fetch(`${API_URL}/feedback/stats`, { headers }),
          fetch(`${API_URL}/ingest?user_id=${userId}`, { headers }).catch(() => null),
        ]);

        const newActivities: ActivityItem[] = [];

        if (feedbackRes.ok) {
          const data = await feedbackRes.json();
          if (data.thumbs_up > 0) {
            newActivities.push({
              icon: "\ud83d\udc4d",
              title: `${data.thumbs_up} positive feedback received`,
              time: "Recent",
            });
          }
          if (data.rewrites > 0) {
            newActivities.push({
              icon: "\u270f\ufe0f",
              title: `${data.rewrites} responses rewritten`,
              time: "Recent",
            });
          }
        }

        if (newActivities.length === 0) {
          newActivities.push(
            { icon: "\ud83d\udcac", title: "Welcome to PersonaAI!", time: "Just now" },
            { icon: "\ud83e\udde0", title: "Start chatting to build your AI twin", time: "Just now" },
            { icon: "\u2705", title: "Complete onboarding to unlock features", time: "Just now" }
          );
        }

        setActivities(newActivities);
      } catch (error) {
        console.error("Failed to fetch activities:", error);
      }
    };

    fetchActivities();
  }, [userId]);

  return (
    <div className="flex h-full flex-col rounded-xl bg-surface p-6 ring-1 ring-foreground/10">
      <h2 className="mb-4 text-lg font-semibold text-white">Recent Activity</h2>
      <ul className="flex flex-1 flex-col">
        {activities.map((activity, index) => (
          <motion.li
            key={`${activity.title}-${index}`}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 + index * 0.08, duration: 0.4 }}
            className="flex items-start gap-3 border-b border-border py-4 transition-colors last:border-b-0 hover:bg-white/[0.03] first:pt-0 last:pb-0"
          >
            <span className="mt-0.5 text-lg leading-none" aria-hidden>
              {activity.icon}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-white">{activity.title}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {activity.time}
              </p>
            </div>
          </motion.li>
        ))}
      </ul>
    </div>
  );
}
