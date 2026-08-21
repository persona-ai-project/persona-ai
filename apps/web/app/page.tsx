"use client";

import { motion } from "framer-motion";
import Link from "next/link";

export default function Home() {
  return (
    <main className="relative min-h-screen bg-background">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-background/80 backdrop-blur-md border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gold-500/10 flex items-center justify-center">
            <svg className="w-5 h-5 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
            </svg>
          </div>
          <span className="text-lg font-bold text-foreground">PersonaAI</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Sign in
          </Link>
          <Link href="/signup" className="px-4 py-2 rounded-lg bg-foreground text-background text-sm font-semibold hover:bg-foreground/90 transition-colors">
            Get started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold-500/10 border border-gold-500/20 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-gold-500 animate-pulse" />
            <span className="text-xs font-medium text-gold-500">Now in private beta for founders</span>
          </motion.div>

          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="text-5xl sm:text-7xl font-bold text-foreground tracking-tight mb-6">
            Your mind,{" "}
            <span className="bg-gradient-to-r from-gold-400 to-gold-600 bg-clip-text text-transparent">
              cloned into AI.
            </span>
          </motion.h1>

          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="text-lg text-muted-foreground max-w-2xl mx-auto mb-10">
            PersonaAI interviews you in a real conversation — voice or text — then builds a digital twin that thinks, answers, and advises the way you do.
          </motion.p>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="flex items-center justify-center gap-4">
            <Link href="/signup" className="btn-gold inline-flex items-center gap-2 px-6 py-3 rounded-lg text-sm font-semibold text-primary-foreground">
              Build your twin
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>
            <Link href="/directory" className="px-6 py-3 rounded-lg border border-white/10 text-sm font-semibold text-foreground hover:bg-white/5 transition-colors">
              Explore twins
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Sample Chat Card */}
      <section className="px-4 pb-16">
        <div className="max-w-2xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="bg-card rounded-2xl border border-white/[0.06] overflow-hidden">
            <div className="flex items-center gap-3 p-4 border-b border-white/[0.06]">
              <div className="w-10 h-10 rounded-xl bg-gold-500 flex items-center justify-center text-primary-foreground font-bold text-sm">SG</div>
              <div>
                <p className="font-semibold text-foreground text-sm">Sareem Gauri — Digital Twin</p>
                <p className="text-xs text-muted-foreground">Founder · 3 startups · 94% fidelity</p>
              </div>
            </div>
            <div className="p-4 space-y-3">
              <div className="flex justify-end">
                <div className="bg-gold-500 text-primary-foreground rounded-2xl rounded-br-md px-4 py-2.5 max-w-[80%] text-sm">
                  How do you decide when to pivot a product?
                </div>
              </div>
              <div className="flex justify-start">
                <div className="bg-white/5 text-foreground rounded-2xl rounded-bl-md px-4 py-2.5 max-w-[80%] text-sm border border-white/[0.06]">
                  I pivot when the cost of continuing exceeds the option value of what I&apos;d learn. Numbers tell you when to stop — conviction tells you what to start next.
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Feature Cards */}
      <section className="px-4 pb-20">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-4">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }} className="bg-card rounded-xl p-6 border border-white/[0.06]">
            <div className="w-10 h-10 rounded-lg bg-gold-500/10 flex items-center justify-center mb-4">
              <svg className="w-5 h-5 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
              </svg>
            </div>
            <h3 className="font-semibold text-foreground mb-2">Conversational interview</h3>
            <p className="text-sm text-muted-foreground">A 15-minute voice or text interview adapts to what you say — no boring forms, no static questionnaires.</p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }} className="bg-card rounded-xl p-6 border border-white/[0.06]">
            <div className="w-10 h-10 rounded-lg bg-gold-500/10 flex items-center justify-center mb-4">
              <svg className="w-5 h-5 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5" />
              </svg>
            </div>
            <h3 className="font-semibold text-foreground mb-2">Knowledge with provenance</h3>
            <p className="text-sm text-muted-foreground">Every answer your twin gives traces back to the source it learned from. Trust, not hallucination.</p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.8 }} className="bg-card rounded-xl p-6 border border-white/[0.06]">
            <div className="w-10 h-10 rounded-lg bg-gold-500/10 flex items-center justify-center mb-4">
              <svg className="w-5 h-5 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
              </svg>
            </div>
            <h3 className="font-semibold text-foreground mb-2">Always-on access</h3>
            <p className="text-sm text-muted-foreground">Your twin mentors, advises, and answers while you sleep — a scalable version of your judgment.</p>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/[0.06] py-8 px-4">
        <p className="text-center text-sm text-muted-foreground">
          &copy; 2026 PersonaAI &middot; Built for founders who think differently.
        </p>
      </footer>
    </main>
  );
}
