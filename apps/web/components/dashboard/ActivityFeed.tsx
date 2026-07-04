"use client";

import { motion } from "framer-motion";

interface ActivityItem {
  icon: string;
  title: string;
  time: string;
}

const ACTIVITIES: ActivityItem[] = [
  { icon: "💬", title: "Asked about career goals", time: "2 mins ago" },
  {
    icon: "🧠",
    title: "New memory stored: leadership style",
    time: "1 hour ago",
  },
  { icon: "✅", title: "Onboarding step 3 completed", time: "3 hours ago" },
  { icon: "💬", title: "Discussed technical skills", time: "Yesterday" },
  {
    icon: "🧠",
    title: "Persona trait updated: Analytical",
    time: "2 days ago",
  },
];

export function ActivityFeed() {
  return (
    <div className="flex h-full flex-col rounded-xl bg-surface p-6 ring-1 ring-foreground/10">
      <h2 className="mb-4 text-lg font-semibold text-white">Recent Activity</h2>
      <ul className="flex flex-1 flex-col">
        {ACTIVITIES.map((activity, index) => (
          <motion.li
            key={activity.title}
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
