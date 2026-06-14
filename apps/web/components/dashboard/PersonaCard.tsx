"use client";

import { motion } from "framer-motion";
import Link from "next/link";

import { CompletenessRing } from "@/components/dashboard/CompletenessRing";
import { TraitBadges } from "@/components/dashboard/TraitBadges";
import { Button } from "@/components/ui/button";

export function PersonaCard() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.15 }}
      className="flex h-full flex-col rounded-xl bg-surface p-6 ring-1 ring-foreground/10"
    >
      <div className="mb-6 text-center">
        <h2 className="text-xl font-semibold text-white">Your AI Twin</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Faizan Afzal • CS Student &amp; AI Builder
        </p>
      </div>

      <div className="mb-6 flex justify-center">
        <CompletenessRing percentage={73} />
      </div>

      <div className="mb-8">
        <TraitBadges />
      </div>

      <div className="mt-auto">
        <Button render={<Link href="/chat" />} className="w-full" size="lg">
          Continue Chat
        </Button>
      </div>
    </motion.div>
  );
}
