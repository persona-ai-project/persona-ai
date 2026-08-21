"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { NavBar } from "@/components/layout/NavBar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { API_URL } from "@/lib/config";

interface Overview {
  total_users: number;
  total_twins: number;
  total_chats: number;
  total_messages: number;
  total_sources: number;
  total_knowledge_items: number;
  active_twins: number;
  public_twins: number;
  avg_fidelity: number | null;
}

interface Engagement {
  daily_active_users: number;
  weekly_active_users: number;
  monthly_active_users: number;
  avg_messages_per_session: number;
  peak_hours: { hour: number; count: number }[];
}

interface TrendPoint {
  date: string;
  count: number;
}

export function AnalyticsDashboard() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [trendMetric, setTrendMetric] = useState("chats");
  const [trendPeriod, setTrendPeriod] = useState("daily");

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchTrends();
  }, [trendMetric, trendPeriod]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("access_token") || "";
      const headers = { Authorization: `Bearer ${token}` };

      const [overviewRes, engagementRes] = await Promise.all([
        fetch(`${API_URL}/analytics/overview`, { headers }),
        fetch(`${API_URL}/analytics/engagement`, { headers }),
      ]);

      if (overviewRes.ok) setOverview(await overviewRes.json());
      if (engagementRes.ok) setEngagement(await engagementRes.json());
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTrends = async () => {
    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(
        `${API_URL}/analytics/trends?metric=${trendMetric}&period=${trendPeriod}&days=30`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setTrends(data.data || []);
      }
    } catch (error) {
      console.error("Failed to fetch trends:", error);
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const getFidelityColor = (score: number | null) => {
    if (!score) return "text-gray-400";
    if (score >= 0.7) return "text-green-400";
    if (score >= 0.4) return "text-yellow-400";
    return "text-red-400";
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <AuthGuard>
    <div className="min-h-dvh bg-background">
      <NavBar title="Analytics" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <p className="text-muted-foreground">Platform insights and metrics</p>
      </div>

      {/* Overview Cards */}
      {overview && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0 }}
          >
            <Card>
              <CardContent className="py-4">
                <p className="text-sm text-muted-foreground">Total Users</p>
                <p className="text-2xl font-bold text-white">
                  {formatNumber(overview.total_users)}
                </p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card>
              <CardContent className="py-4">
                <p className="text-sm text-muted-foreground">Total Twins</p>
                <p className="text-2xl font-bold text-white">
                  {formatNumber(overview.total_twins)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {overview.public_twins} public
                </p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card>
              <CardContent className="py-4">
                <p className="text-sm text-muted-foreground">Total Chats</p>
                <p className="text-2xl font-bold text-white">
                  {formatNumber(overview.total_chats)}
                </p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card>
              <CardContent className="py-4">
                <p className="text-sm text-muted-foreground">Avg Fidelity</p>
                <p className={`text-2xl font-bold ${getFidelityColor(overview.avg_fidelity)}`}>
                  {overview.avg_fidelity
                    ? `${(overview.avg_fidelity * 100).toFixed(0)}%`
                    : "N/A"}
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      )}

      {/* Detailed Stats */}
      {overview && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardContent className="py-4">
              <p className="text-sm text-muted-foreground">Total Messages</p>
              <p className="text-2xl font-bold text-white">
                {formatNumber(overview.total_messages)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="py-4">
              <p className="text-sm text-muted-foreground">Total Sources</p>
              <p className="text-2xl font-bold text-white">
                {formatNumber(overview.total_sources)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="py-4">
              <p className="text-sm text-muted-foreground">Knowledge Items</p>
              <p className="text-2xl font-bold text-white">
                {formatNumber(overview.total_knowledge_items)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Engagement & Trends */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Engagement */}
        {engagement && (
          <Card>
            <CardHeader>
              <CardTitle>Engagement</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Daily Active</p>
                  <p className="text-xl font-bold text-white">
                    {formatNumber(engagement.daily_active_users)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Weekly Active</p>
                  <p className="text-xl font-bold text-white">
                    {formatNumber(engagement.weekly_active_users)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Monthly Active</p>
                  <p className="text-xl font-bold text-white">
                    {formatNumber(engagement.monthly_active_users)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Avg Messages/Session</p>
                  <p className="text-xl font-bold text-white">
                    {engagement.avg_messages_per_session.toFixed(1)}
                  </p>
                </div>
              </div>

              {engagement.peak_hours.length > 0 && (
                <div>
                  <p className="mb-2 text-sm font-medium text-muted-foreground">
                    Peak Hours (Last 7 Days)
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {engagement.peak_hours.map((peak) => (
                      <Badge key={peak.hour} variant="secondary">
                        {peak.hour}:00 ({peak.count})
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Trends */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Trends</CardTitle>
            <div className="flex gap-2">
              <Select value={trendMetric} onValueChange={setTrendMetric}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="chats">Chats</SelectItem>
                  <SelectItem value="messages">Messages</SelectItem>
                  <SelectItem value="knowledge">Knowledge</SelectItem>
                  <SelectItem value="sources">Sources</SelectItem>
                </SelectContent>
              </Select>

              <Select value={trendPeriod} onValueChange={setTrendPeriod}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            {trends.length === 0 ? (
              <p className="py-8 text-center text-muted-foreground">
                No trend data available
              </p>
            ) : (
              <div className="space-y-2">
                {trends.slice(-10).map((point, index) => (
                  <div key={point.date} className="flex items-center gap-4">
                    <span className="w-24 text-xs text-muted-foreground">
                      {new Date(point.date).toLocaleDateString()}
                    </span>
                    <div className="flex-1">
                      <div
                        className="h-4 rounded bg-primary/20"
                        style={{
                          width: `${Math.min(
                            (point.count / Math.max(...trends.map((t) => t.count))) * 100,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                    <span className="w-12 text-right text-sm font-medium text-white">
                      {point.count}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
    </div>
    </AuthGuard>
  );
}
