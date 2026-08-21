"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface AuthCardProps {
  heading: string;
  subheading: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}

export function AuthCard({
  heading,
  subheading,
  children,
  footer,
  icon,
  className,
}: AuthCardProps) {
  return (
    <main className="relative flex min-h-screen items-center justify-center bg-background px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className={cn("relative z-10 w-full max-w-[420px]", className)}
      >
        <div className="flex flex-col items-center mb-8">
          {icon && (
            <div className="w-14 h-14 rounded-2xl bg-gold-500/10 flex items-center justify-center mb-4">
              {icon}
            </div>
          )}
          <h1 className="text-3xl font-bold text-foreground">{heading}</h1>
          <p className="text-muted-foreground mt-1">{subheading}</p>
        </div>

        <div className="bg-card rounded-2xl border border-white/[0.06] p-6">
          {children}
        </div>

        {footer && (
          <p className="text-center text-sm text-muted-foreground mt-6">
            {footer}
          </p>
        )}
      </motion.div>
    </main>
  );
}
