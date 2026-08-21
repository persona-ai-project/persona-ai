"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/config";

interface PublicTwin {
  id: string;
  name: string;
  slug: string;
  tagline: string | null;
  role: string | null;
  expertise: string[];
  accent_color: string;
  status: string;
  chat_count: number;
}

const ACCENT_BG: Record<string, string> = {
  purple: "bg-twin-purple",
  blue: "bg-twin-blue",
  green: "bg-twin-green",
  pink: "bg-twin-pink",
  yellow: "bg-twin-yellow",
  teal: "bg-twin-teal",
  gold: "bg-gold-500",
};

export default function DirectoryPage() {
  const router = useRouter();
  const [twins, setTwins] = useState<PublicTwin[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchTwins();
  }, []);

  const fetchTwins = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      const res = await fetch(`${API_URL}/twins/public?${params}`);
      if (res.ok) {
        const data = await res.json();
        setTwins(data.twins || []);
      }
    } catch (e) {
      console.error("Failed to fetch twins:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchTwins();
  };

  const getInitials = (name: string) =>
    name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded-lg bg-gold-500/10 flex items-center justify-center">
            <svg className="w-4 h-4 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-foreground">Discover twins</h1>
        </div>
        <p className="text-muted-foreground text-sm">
          Chat with digital twins of founders, experts, and thinkers.
        </p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="relative max-w-xl">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or expertise..."
            className="w-full bg-card border border-white/[0.06] rounded-xl pl-10 pr-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-gold-500/50 transition-colors"
          />
        </div>
      </form>

      {/* Twins Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : twins.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-muted-foreground">No twins found. Try a different search.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {twins.map((twin, i) => (
            <motion.div
              key={twin.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => router.push(`/t/${twin.slug}`)}
              className="twin-card cursor-pointer"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold text-white ${ACCENT_BG[twin.accent_color] || "bg-gold-500"}`}>
                  {getInitials(twin.name)}
                </div>
                <span className="text-[11px] font-medium px-2 py-0.5 rounded-full badge-live">
                  ● live
                </span>
              </div>

              <h3 className="font-semibold text-foreground mb-1">{twin.name}</h3>
              <p className="text-sm text-muted-foreground mb-3">
                {twin.role || twin.tagline || "Digital Twin"}
              </p>

              {twin.expertise && twin.expertise.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {twin.expertise.slice(0, 3).map((skill) => (
                    <span key={skill} className="tag">{skill}</span>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 011.037-.443 48.282 48.282 0 005.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
                </svg>
                {twin.chat_count || 0} chats
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
