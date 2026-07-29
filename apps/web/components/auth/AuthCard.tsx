"use client";

import { motion } from "framer-motion";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

function PersonaAILogo() {
  return (
    <h1 className="text-xl font-semibold tracking-tight text-primary sm:text-2xl">
      PersonaAI
    </h1>
  );
}

interface AuthCardProps {
  heading: string;
  subheading: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export function AuthCard({
  heading,
  subheading,
  children,
  footer,
  className,
}: AuthCardProps) {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#0a0a1a] px-4 py-8">
      <motion.div
        className="pointer-events-none absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#8b5cf6] opacity-20 blur-[100px] sm:h-96 sm:w-96"
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
        className="pointer-events-none absolute left-1/2 top-1/2 h-48 w-48 -translate-x-1/2 -translate-y-1/2 rounded-full bg-purple-400 opacity-10 blur-[80px] sm:h-72 sm:w-72"
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

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className={cn("relative z-10 w-full max-w-[420px]", className)}
      >
        <div className="relative w-full rounded-2xl p-[2px]">
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary via-purple-400 to-primary/50" />
          <Card className="relative border-0 bg-surface shadow-2xl">
            <CardContent className="flex flex-col gap-6 p-6 sm:p-8">
              <div className="flex flex-col items-center gap-2 text-center">
                <PersonaAILogo />
                <h2 className="text-2xl font-bold tracking-tight text-foreground">
                  {heading}
                </h2>
                <p className="text-sm text-muted-foreground">{subheading}</p>
              </div>

              {children}

              {footer ? (
                <p className="text-center text-sm text-muted-foreground">
                  {footer}
                </p>
              ) : null}
            </CardContent>
          </Card>
        </div>
      </motion.div>
    </main>
  );
}
