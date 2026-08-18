"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { PersonaCard } from "@/components/dashboard/PersonaCard";
import { QuickStats } from "@/components/dashboard/QuickStats";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { API_URL } from "@/lib/config";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/owner", label: "My Twins" },
  { href: "/directory", label: "Directory" },
  { href: "/chat", label: "Chat" },
  { href: "/subscription", label: "Subscription" },
  { href: "/onboarding", label: "Onboarding" },
] as const;

export function DashboardContent() {
  const pathname = usePathname();
  const [persona, setPersona] = useState<any>(null);
  const [completeness, setCompleteness] = useState(0);
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const storedUserId = localStorage.getItem("user_id");
    if (storedUserId) {
      setUserId(storedUserId);
    }
  }, []);

  useEffect(() => {
    if (!userId) return;

    const fetchData = async () => {
      try {
        const token = localStorage.getItem("access_token") || "";
        const headers = { "Authorization": `Bearer ${token}` };

        const [personaRes, completenessRes] = await Promise.all([
          fetch(`${API_URL}/persona/${userId}`, { headers }),
          fetch(`${API_URL}/persona/${userId}/completeness`, { headers }),
        ]);

        if (personaRes.ok) {
          const data = await personaRes.json();
          setPersona(data);
        }

        if (completenessRes.ok) {
          const data = await completenessRes.json();
          setCompleteness(data.completeness * 100);
        }
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      }
    };

    fetchData();
  }, [userId]);

  const displayName = persona?.name || "Your AI Twin";
  const initials = displayName
    .split(" ")
    .map((n: string) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

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
                {initials || "U"}
              </AvatarFallback>
            </Avatar>
            <span className="hidden text-sm font-medium text-white sm:inline">
              {displayName}
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
        <QuickStats userId={userId} />

        <div className="grid gap-6 lg:grid-cols-2">
          <PersonaCard persona={persona} completeness={completeness} />
          <ActivityFeed userId={userId} />
        </div>

        {persona && (
          <section>
            <h2 className="mb-4 text-lg font-semibold text-white">
              Persona Insights
            </h2>
            <div className="grid gap-4 md:grid-cols-3">
              {persona.personality && (
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4, duration: 0.4 }}
                  className="rounded-xl border-l-4 border-l-primary bg-surface p-5 ring-1 ring-foreground/10 transition-colors hover:ring-primary/30"
                >
                  <h3 className="mb-2 font-medium text-white">Communication Style</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {persona.personality}
                  </p>
                </motion.div>
              )}
              {persona.profession && (
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5, duration: 0.4 }}
                  className="rounded-xl border-l-4 border-l-primary bg-surface p-5 ring-1 ring-foreground/10 transition-colors hover:ring-primary/30"
                >
                  <h3 className="mb-2 font-medium text-white">Professional Focus</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {persona.profession}
                  </p>
                </motion.div>
              )}
              {persona.background && (
                <motion.div
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6, duration: 0.4 }}
                  className="rounded-xl border-l-4 border-l-primary bg-surface p-5 ring-1 ring-foreground/10 transition-colors hover:ring-primary/30"
                >
                  <h3 className="mb-2 font-medium text-white">Background</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {persona.background}
                  </p>
                </motion.div>
              )}
            </div>
          </section>
        )}
      </motion.main>
    </div>
  );
}
