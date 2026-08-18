"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { API_URL } from "@/lib/config";

interface Plan {
  id: string;
  name: string;
  display_name: string;
  description: string | null;
  max_twins: number;
  max_sources_per_twin: number;
  max_messages_per_day: number;
  max_interview_sessions: number;
  features: string[] | null;
  price_monthly: number | null;
  price_yearly: number | null;
}

interface Subscription {
  id: string;
  plan: Plan;
  status: string;
  current_period_start: string | null;
  current_period_end: string | null;
  created_at: string;
}

interface Usage {
  twins_used: number;
  twins_limit: number;
  sources_used: number;
  sources_limit: number;
  messages_today: number;
  messages_limit: number;
  interviews_used: number;
  interviews_limit: number;
}

export function SubscriptionManager() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(true);
  const [changing, setChanging] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("access_token") || "";
      const headers = { Authorization: `Bearer ${token}` };

      const [subRes, plansRes, usageRes] = await Promise.all([
        fetch(`${API_URL}/subscriptions/me`, { headers }),
        fetch(`${API_URL}/subscriptions/plans`),
        fetch(`${API_URL}/subscriptions/me/usage`, { headers }),
      ]);

      if (subRes.ok) setSubscription(await subRes.json());
      if (plansRes.ok) setPlans(await plansRes.json());
      if (usageRes.ok) setUsage(await usageRes.json());
    } catch (error) {
      console.error("Failed to fetch subscription data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePlan = async (planName: string) => {
    if (!confirm(`Are you sure you want to change to the ${planName} plan?`)) {
      return;
    }

    setChanging(true);
    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/subscriptions/change`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ plan_name: planName }),
      });

      if (res.ok) {
        await fetchData();
        alert("Plan changed successfully!");
      } else {
        const data = await res.json();
        alert(data.detail || "Failed to change plan");
      }
    } catch (error) {
      alert("Failed to change plan");
    } finally {
      setChanging(false);
    }
  };

  const formatPrice = (price: number | null) => {
    if (price === null) return "Free";
    return `$${(price / 100).toFixed(2)}`;
  };

  const getUsagePercentage = (used: number, limit: number) => {
    if (limit === 0) return 0;
    return Math.min((used / limit) * 100, 100);
  };

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return "text-red-400";
    if (percentage >= 70) return "text-yellow-400";
    return "text-green-400";
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Current Plan */}
      {subscription && (
        <Card className="border-primary/20">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Current Plan</CardTitle>
              <Badge className="bg-primary/20 text-primary">
                {subscription.plan.display_name}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              {subscription.plan.description}
            </p>

            {subscription.current_period_end && (
              <p className="text-sm text-muted-foreground">
                Renews: {new Date(subscription.current_period_end).toLocaleDateString()}
              </p>
            )}

            {/* Usage */}
            {usage && (
              <div className="space-y-4">
                <h4 className="font-medium text-white">Usage</h4>

                <div className="space-y-3">
                  <div>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Twins</span>
                      <span className={getUsageColor(getUsagePercentage(usage.twins_used, usage.twins_limit))}>
                        {usage.twins_used} / {usage.twins_limit}
                      </span>
                    </div>
                    <Progress value={getUsagePercentage(usage.twins_used, usage.twins_limit)} />
                  </div>

                  <div>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Sources (per twin)</span>
                      <span className={getUsageColor(getUsagePercentage(usage.sources_used, usage.sources_limit))}>
                        {usage.sources_used} / {usage.sources_limit}
                      </span>
                    </div>
                    <Progress value={getUsagePercentage(usage.sources_used, usage.sources_limit)} />
                  </div>

                  <div>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Messages Today</span>
                      <span className={getUsageColor(getUsagePercentage(usage.messages_today, usage.messages_limit))}>
                        {usage.messages_today} / {usage.messages_limit}
                      </span>
                    </div>
                    <Progress value={getUsagePercentage(usage.messages_today, usage.messages_limit)} />
                  </div>

                  <div>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Interview Sessions</span>
                      <span className={getUsageColor(getUsagePercentage(usage.interviews_used, usage.interviews_limit))}>
                        {usage.interviews_used} / {usage.interviews_limit}
                      </span>
                    </div>
                    <Progress value={getUsagePercentage(usage.interviews_used, usage.interviews_limit)} />
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Available Plans */}
      <div>
        <h2 className="mb-4 text-xl font-semibold text-white">Available Plans</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan, index) => {
            const isCurrent = subscription?.plan.name === plan.name;
            const isFree = plan.price_monthly === null;

            return (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className={`h-full ${isCurrent ? "border-primary" : ""}`}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>{plan.display_name}</CardTitle>
                      {isCurrent && <Badge>Current</Badge>}
                    </div>
                    <div className="mt-2">
                      <span className="text-3xl font-bold text-white">
                        {isFree ? "Free" : formatPrice(plan.price_monthly)}
                      </span>
                      {!isFree && (
                        <span className="text-muted-foreground">/month</span>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground">
                      {plan.description}
                    </p>

                    <ul className="space-y-2 text-sm">
                      <li className="flex items-center gap-2">
                        <span className="text-green-400">✓</span>
                        <span>{plan.max_twins} twin{plan.max_twins > 1 ? "s" : ""}</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="text-green-400">✓</span>
                        <span>{plan.max_sources_per_twin} sources per twin</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="text-green-400">✓</span>
                        <span>{plan.max_messages_per_day} messages/day</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="text-green-400">✓</span>
                        <span>{plan.max_interview_sessions} interview sessions</span>
                      </li>
                    </ul>

                    {plan.features && plan.features.length > 0 && (
                      <div className="pt-2">
                        <p className="mb-2 text-xs font-medium text-muted-foreground">
                          Features:
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {plan.features.map((feature, i) => (
                            <Badge key={i} variant="secondary" className="text-xs">
                              {feature}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    <Button
                      className="w-full mt-4"
                      variant={isCurrent ? "outline" : "default"}
                      disabled={isCurrent || changing}
                      onClick={() => handleChangePlan(plan.name)}
                    >
                      {isCurrent ? "Current Plan" : "Select Plan"}
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Note */}
      <Card className="border-yellow-500/20 bg-yellow-500/5">
        <CardContent className="py-4">
          <p className="text-sm text-muted-foreground">
            <strong>Note:</strong> This is a mock implementation. In production, plan changes would
            integrate with Stripe for payment processing and billing management.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
