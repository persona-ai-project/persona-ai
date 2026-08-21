"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/config";

interface Twin {
  id: string;
  name: string;
  tagline: string;
  role: string;
  bio: string;
  expertise: string[];
  accent_color: string;
  status: string;
  chat_count: number;
  is_public: boolean;
  created_at: string;
}

const ACCENT_COLORS: Record<string, string> = {
  purple: "border-twin-purple",
  blue: "border-twin-blue",
  green: "border-twin-green",
  pink: "border-twin-pink",
  yellow: "border-twin-yellow",
  teal: "border-twin-teal",
  gold: "border-gold-500",
};

const ACCENT_BG: Record<string, string> = {
  purple: "bg-twin-purple",
  blue: "bg-twin-blue",
  green: "bg-twin-green",
  pink: "bg-twin-pink",
  yellow: "bg-twin-yellow",
  teal: "bg-twin-teal",
  gold: "bg-gold-500",
};

const STATUS_BADGE: Record<string, string> = {
  training: "badge-training",
  live: "badge-live",
  draft: "badge-draft",
};

export default function DashboardPage() {
  const router = useRouter();
  const [twins, setTwins] = useState<Twin[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTwins();
  }, []);

  const fetchTwins = async () => {
    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/twins`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setTwins(data.twins || data || []);
      }
    } catch (e) {
      console.error("Failed to fetch twins:", e);
    } finally {
      setLoading(false);
    }
  };

  const totalTwins = twins.length;
  const liveTwins = twins.filter((t) => t.status === "live").length;
  const totalChats = twins.reduce((sum, t) => sum + (t.chat_count || 0), 0);
  const avgFidelity = totalTwins > 0 ? Math.round((liveTwins / totalTwins) * 100) : 0;

  const getInitials = (name: string) =>
    name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Your digital twins</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Create, train, and monitor the AI versions of minds you admire.
          </p>
        </div>
        <button
          onClick={() => router.push("/create")}
          className="btn-gold flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold text-primary-foreground"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New twin
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Total twins", value: totalTwins, icon: "👥" },
          { label: "Live twins", value: liveTwins, icon: "📈" },
          { label: "Total chats", value: totalChats, icon: "💬" },
          { label: "Avg. fidelity", value: `${avgFidelity}%`, icon: "🎯" },
        ].map((stat) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-card rounded-xl p-4 border border-white/[0.06]"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">{stat.label}</span>
              <span className="text-sm">{stat.icon}</span>
            </div>
            <p className="text-2xl font-bold text-foreground">{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Twins Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : twins.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-muted-foreground mb-4">No twins yet. Create your first one!</p>
          <button
            onClick={() => router.push("/create")}
            className="btn-gold px-6 py-2.5 rounded-lg text-sm font-semibold text-primary-foreground"
          >
            Create Twin
          </button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {twins.map((twin, i) => (
            <motion.div
              key={twin.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => router.push(`/twins/${twin.id}/chat`)}
              className={`twin-card cursor-pointer border-l-4 ${
                ACCENT_COLORS[twin.accent_color] || "border-gold-500"
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold text-white ${
                    ACCENT_BG[twin.accent_color] || "bg-gold-500"
                  }`}
                >
                  {getInitials(twin.name)}
                </div>
                <span
                  className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                    STATUS_BADGE[twin.status] || "badge-draft"
                  }`}
                >
                  ● {twin.status || "draft"}
                </span>
              </div>

              <h3 className="font-semibold text-foreground mb-1">{twin.name}</h3>
              <p className="text-sm text-muted-foreground mb-3 line-clamp-1">
                {twin.role || twin.tagline || "Digital Twin"}
              </p>

              {twin.expertise && twin.expertise.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {twin.expertise.slice(0, 3).map((skill) => (
                    <span key={skill} className="tag">
                      {skill}
                    </span>
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
