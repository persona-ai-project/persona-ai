"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { PersonaCard } from "@/components/dashboard/PersonaCard";
import { QuickStats } from "@/components/dashboard/QuickStats";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/chat", label: "Chat" },
  { href: "/onboarding", label: "Onboarding" },
] as const;

const INSIGHTS = [
  {
    title: "Communication Style",
    description:
      "Direct and data-driven. You prefer structured information.",
  },
  {
    title: "Learning Pattern",
    description:
      "Visual learner who connects concepts to real-world applications.",
  },
  {
    title: "Work Style",
    description: "Systems thinker who focuses on leverage and scale.",
  },
] as const;

export function DashboardContent() {
  const pathname = usePathname();

  return (
    <div className="min-h-dvh bg-background">
      <header className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur-sm">
        <div className="relative mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <Link
            href="/dashboard"
            className="text-lg font-semibold tracking-tight text-primary sm:text-xl"
          >
            PersonaAI
          </Link>

          <h1 className="absolute left-1/2 hidden -translate-x-1/2 text-sm font-medium text-foreground sm:block sm:text-base">
            Dashboard
          </h1>

          <div className="flex items-center gap-2 sm:gap-3">
            <Avatar size="sm">
              <AvatarFallback className="bg-primary text-xs font-semibold text-primary-foreground">
                F
              </AvatarFallback>
            </Avatar>
            <span className="hidden text-sm font-medium text-white sm:inline">
              Faizan Afzal
            </span>
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

      <motion.main
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 sm:py-8"
      >
        <QuickStats />

        <div className="grid gap-6 lg:grid-cols-2">
          <PersonaCard />
          <ActivityFeed />
        </div>

        <section>
          <h2 className="mb-4 text-lg font-semibold text-white">
            Persona Insights
          </h2>
          <div className="grid gap-4 md:grid-cols-3">
            {INSIGHTS.map((insight, index) => (
              <motion.div
                key={insight.title}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + index * 0.1, duration: 0.4 }}
                className="rounded-xl border-l-4 border-l-primary bg-surface p-5 ring-1 ring-foreground/10 transition-colors hover:ring-primary/30"
              >
                <h3 className="mb-2 font-medium text-white">{insight.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {insight.description}
                </p>
              </motion.div>
            ))}
          </div>
        </section>
      </motion.main>
    </div>
  );
}
