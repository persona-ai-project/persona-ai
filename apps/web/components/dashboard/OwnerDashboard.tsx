"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { CreateTwinModal } from "@/components/dashboard/CreateTwinModal";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { NavBar } from "@/components/layout/NavBar";
import { API_URL } from "@/lib/config";

interface Twin {
  id: string;
  name: string;
  slug: string;
  tagline: string | null;
  status: string;
  visibility: string;
  total_chats: number;
  avg_fidelity: number | null;
  created_at: string;
  category_name: string | null;
}

interface Subscription {
  plan_name: string;
  max_twins: number;
  twins_used: number;
}

export function OwnerDashboard() {
  const router = useRouter();
  const [twins, setTwins] = useState<Twin[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    fetchTwins();
    fetchSubscription();
  }, []);

  const fetchTwins = async () => {
    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/twins?limit=50`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setTwins(data.twins || []);
      }
    } catch (error) {
      console.error("Failed to fetch twins:", error);
    }
  };

  const fetchSubscription = async () => {
    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSubscription(data.subscription || { plan_name: "free", max_twins: 1, twins_used: 0 });
      }
    } catch (error) {
      console.error("Failed to fetch subscription:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTwin = (twin: Twin) => {
    setTwins([twin, ...twins]);
    setShowCreateModal(false);
    router.push(`/twins/${twin.id}`);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "bg-green-500/20 text-green-400";
      case "draft": return "bg-yellow-500/20 text-yellow-400";
      case "archived": return "bg-gray-500/20 text-gray-400";
      default: return "bg-gray-500/20 text-gray-400";
    }
  };

  const getVisibilityIcon = (visibility: string) => {
    switch (visibility) {
      case "public": return "🌐";
      case "unlisted": return "🔗";
      case "private": return "🔒";
      default: return "🔒";
    }
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
      <NavBar title="My Twins" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Your Twins</h1>
          <p className="text-muted-foreground">
            Create and manage your AI digital twins
          </p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          disabled={subscription ? subscription.twins_used >= subscription.max_twins : false}
        >
          + Create Twin
        </Button>
      </div>

      {/* Subscription Banner */}
      {subscription && (
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="flex items-center justify-between py-4">
            <div>
              <p className="text-sm font-medium text-white">
                {subscription.plan_name.charAt(0).toUpperCase() + subscription.plan_name.slice(1)} Plan
              </p>
              <p className="text-xs text-muted-foreground">
                {subscription.twins_used} / {subscription.max_twins} twins used
              </p>
            </div>
            {subscription.twins_used >= subscription.max_twins && (
              <Button variant="outline" size="sm" onClick={() => router.push("/subscription")}>
                Upgrade
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Twins Grid */}
      {twins.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="mb-4 text-4xl">🤖</div>
            <h3 className="mb-2 text-lg font-medium text-white">No twins yet</h3>
            <p className="mb-4 text-center text-sm text-muted-foreground">
              Create your first AI twin to get started
            </p>
            <Button onClick={() => setShowCreateModal(true)}>
              + Create Your First Twin
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {twins.map((twin, index) => (
            <motion.div
              key={twin.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.3 }}
            >
              <Card
                className="cursor-pointer transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10"
                onClick={() => router.push(`/twins/${twin.id}`)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <Avatar>
                        <AvatarFallback className="bg-primary/20 text-primary">
                          {twin.name.slice(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <CardTitle className="text-base text-white">
                          {twin.name}
                        </CardTitle>
                        {twin.tagline && (
                          <p className="text-xs text-muted-foreground line-clamp-1">
                            {twin.tagline}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <span title={twin.visibility}>
                        {getVisibilityIcon(twin.visibility)}
                      </span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Badge className={getStatusColor(twin.status)}>
                      {twin.status}
                    </Badge>
                    {twin.category_name && (
                      <Badge variant="outline">{twin.category_name}</Badge>
                    )}
                  </div>
                  <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                    <span>{twin.total_chats} chats</span>
                    <span>{new Date(twin.created_at).toLocaleDateString()}</span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Create Twin Modal */}
      <CreateTwinModal
        open={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreateTwin}
      />
      </div>
    </div>
    </AuthGuard>
  );
}
