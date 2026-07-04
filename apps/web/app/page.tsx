"use client";

import { motion } from "framer-motion";
import Link from "next/link";

import { Button } from "@/components/ui/button";

const FEATURES = ["RAG Memory", "Streaming Chat", "Persona Insights"] as const;

export default function Home() {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#0a0a1a] px-4">
      <motion.div
        className="pointer-events-none absolute left-1/2 top-1/3 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#8b5cf6] opacity-20 blur-[100px] sm:h-96 sm:w-96"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.15, 0.25, 0.15],
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <motion.div
        className="pointer-events-none absolute left-1/2 top-1/3 h-48 w-48 -translate-x-1/2 -translate-y-1/2 rounded-full bg-purple-400 opacity-10 blur-[80px] sm:h-72 sm:w-72"
        animate={{
          scale: [1.1, 0.9, 1.1],
          opacity: [0.08, 0.18, 0.08],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 1,
        }}
      />

      <div className="relative z-10 flex w-full max-w-2xl flex-col items-center text-center">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="text-balance text-4xl font-bold tracking-tight text-white sm:text-6xl"
        >
          Meet Your AI Twin
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.15 }}
          className="mt-4 max-w-md text-balance text-base text-[#a1a1b5] sm:text-lg"
        >
          PersonaAI learns who you are and thinks like you.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.3 }}
          className="mt-8"
        >
          <Button
            render={<Link href="/onboarding" />}
            size="lg"
            className="h-12 px-8 text-base"
          >
            Start Onboarding
          </Button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.45 }}
          className="mt-8 flex flex-nowrap items-center justify-center gap-1.5 sm:gap-3"
        >
          {FEATURES.map((feature) => (
            <span
              key={feature}
              className="whitespace-nowrap rounded-full border border-[#8b5cf6]/30 bg-[#8b5cf6]/10 px-2.5 py-1 text-[10px] font-medium text-[#8b5cf6] sm:px-4 sm:py-1.5 sm:text-sm"
            >
              {feature}
            </span>
          ))}
        </motion.div>
      </div>
    </main>
  );
}
