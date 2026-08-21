"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { PersonaCard } from "@/components/dashboard/PersonaCard";
import { QuickStats } from "@/components/dashboard/QuickStats";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { NavBar } from "@/components/layout/NavBar";
import { API_URL } from "@/lib/config";

export function DashboardContent() {
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
    <AuthGuard>
    <div className="min-h-dvh bg-background">
      <NavBar title="Dashboard" initials={initials || "U"} displayName={displayName} />

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
    </AuthGuard>
  );
}
