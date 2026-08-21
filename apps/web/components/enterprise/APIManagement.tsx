"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { NavBar } from "@/components/layout/NavBar";
import { API_URL } from "@/lib/config";

interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  rate_limit: number;
  daily_usage: number;
  last_used_at: string | null;
  expires_at: string | null;
  is_active: boolean;
  created_at: string;
}

interface UsageStats {
  total_requests: number;
  requests_today: number;
  avg_latency_ms: number;
  error_rate: number;
  top_endpoints: { endpoint: string; count: number }[];
  usage_by_day: { date: string; count: number }[];
}

interface Webhook {
  id: string;
  url: string;
  events: string[];
  is_active: boolean;
  last_triggered_at: string | null;
  failure_count: number;
  created_at: string;
}

export function APIManagement() {
  const router = useRouter();
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateKey, setShowCreateKey] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyResult, setNewKeyResult] = useState<string | null>(null);
  const [enterprisePlan, setEnterprisePlan] = useState<any>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("access_token") || "";
      const headers = { Authorization: `Bearer ${token}` };

      const [keysRes, usageRes, webhooksRes, planRes] = await Promise.all([
        fetch(`${API_URL}/enterprise/api-keys`, { headers }),
        fetch(`${API_URL}/enterprise/usage?days=30`, { headers }),
        fetch(`${API_URL}/enterprise/webhooks`, { headers }),
        fetch(`${API_URL}/enterprise/plan`, { headers }),
      ]);

      if (keysRes.ok) setApiKeys(await keysRes.json());
      if (usageRes.ok) setUsageStats(await usageRes.json());
      if (webhooksRes.ok) setWebhooks(await webhooksRes.json());
      if (planRes.ok) setEnterprisePlan(await planRes.json());
    } catch (error) {
      console.error("Failed to fetch API data:", error);
    } finally {
      setLoading(false);
    }
  };

  const createAPIKey = async () => {
    if (!newKeyName.trim()) return;

    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/enterprise/api-keys`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: newKeyName,
          scopes: ["*"],
          rate_limit: 1000,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setNewKeyResult(data.key);
        setNewKeyName("");
        setShowCreateKey(false);
        fetchData();
      }
    } catch (error) {
      console.error("Failed to create API key:", error);
    }
  };

  const revokeAPIKey = async (keyId: string) => {
    if (!confirm("Are you sure you want to revoke this API key?")) return;

    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/enterprise/api-keys/${keyId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        fetchData();
      }
    } catch (error) {
      console.error("Failed to revoke API key:", error);
    }
  };

  const rotateAPIKey = async (keyId: string) => {
    if (!confirm("Rotate this API key? The old key will be invalidated.")) return;

    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/enterprise/api-keys/${keyId}/rotate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        const data = await res.json();
        setNewKeyResult(data.key);
        fetchData();
      }
    } catch (error) {
      console.error("Failed to rotate API key:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!enterprisePlan?.api_access) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center text-center">
        <div className="mb-4 text-6xl">🔐</div>
        <h2 className="mb-2 text-2xl font-bold text-white">Enterprise API Access</h2>
        <p className="mb-6 max-w-md text-muted-foreground">
          API access is available for Enterprise plan subscribers. 
          Upgrade to get programmatic access to your digital twins.
        </p>
        <Button onClick={() => router.push("/subscription")}>
          View Plans
        </Button>
      </div>
    );
  }

  return (
    <AuthGuard>
    <div className="min-h-dvh bg-background">
      <NavBar title="API" />
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">API Management</h1>
          <p className="text-muted-foreground">
            Manage API keys, webhooks, and monitor usage
          </p>
        </div>
        <Badge className="bg-green-500/20 text-green-400">
          Enterprise Plan
        </Badge>
      </div>

      {/* API Key Result Modal */}
      {newKeyResult && (
        <Card className="border-green-500/50">
          <CardHeader>
            <CardTitle className="text-green-400">API Key Created</CardTitle>
            <CardDescription>
              Copy this key now. It won't be shown again.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input
                value={newKeyResult}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                onClick={() => {
                  navigator.clipboard.writeText(newKeyResult);
                  alert("Copied!");
                }}
              >
                Copy
              </Button>
            </div>
            <Button
              variant="ghost"
              className="mt-2"
              onClick={() => setNewKeyResult(null)}
            >
              Close
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Usage Stats */}
      {usageStats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="py-4">
              <p className="text-sm text-muted-foreground">Total Requests (30d)</p>
              <p className="text-2xl font-bold text-white">
                {usageStats.total_requests.toLocaleString()}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4">
              <p className="text-sm text-muted-foreground">Today</p>
              <p className="text-2xl font-bold text-white">
                {usageStats.requests_today.toLocaleString()}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4">
              <p className="text-sm text-muted-foreground">Avg Latency</p>
              <p className="text-2xl font-bold text-white">
                {usageStats.avg_latency_ms.toFixed(0)}ms
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="py-4">
              <p className="text-sm text-muted-foreground">Error Rate</p>
              <p className="text-2xl font-bold text-white">
                {usageStats.error_rate.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs defaultValue="keys" className="w-full">
        <TabsList>
          <TabsTrigger value="keys">API Keys ({apiKeys.length})</TabsTrigger>
          <TabsTrigger value="webhooks">Webhooks ({webhooks.length})</TabsTrigger>
          <TabsTrigger value="docs">Documentation</TabsTrigger>
        </TabsList>

        {/* API Keys Tab */}
        <TabsContent value="keys" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>API Keys</CardTitle>
                <CardDescription>
                  Manage keys for programmatic access
                </CardDescription>
              </div>
              <Button onClick={() => setShowCreateKey(true)}>
                + Create Key
              </Button>
            </CardHeader>
            <CardContent>
              {showCreateKey && (
                <div className="mb-4 flex gap-2">
                  <Input
                    placeholder="Key name (e.g., production-server)"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                  />
                  <Button onClick={createAPIKey}>Create</Button>
                  <Button variant="ghost" onClick={() => setShowCreateKey(false)}>
                    Cancel
                  </Button>
                </div>
              )}

              {apiKeys.length === 0 ? (
                <p className="py-8 text-center text-muted-foreground">
                  No API keys yet. Create one to get started.
                </p>
              ) : (
                <div className="space-y-3">
                  {apiKeys.map((key) => (
                    <div
                      key={key.id}
                      className="flex items-center justify-between rounded-lg border p-4"
                    >
                      <div className="flex items-center gap-4">
                        <div className="font-mono text-sm text-muted-foreground">
                          {key.key_prefix}...
                        </div>
                        <div>
                          <p className="font-medium text-white">{key.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {key.daily_usage}/{key.rate_limit} requests today
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={key.is_active ? "default" : "destructive"}>
                          {key.is_active ? "Active" : "Revoked"}
                        </Badge>
                        {key.is_active && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => rotateAPIKey(key.id)}
                            >
                              Rotate
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => revokeAPIKey(key.id)}
                            >
                              Revoke
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Webhooks Tab */}
        <TabsContent value="webhooks" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Webhooks</CardTitle>
                <CardDescription>
                  Receive real-time event notifications
                </CardDescription>
              </div>
              <Button>+ Create Webhook</Button>
            </CardHeader>
            <CardContent>
              {webhooks.length === 0 ? (
                <p className="py-8 text-center text-muted-foreground">
                  No webhooks configured.
                </p>
              ) : (
                <div className="space-y-3">
                  {webhooks.map((wh) => (
                    <div
                      key={wh.id}
                      className="flex items-center justify-between rounded-lg border p-4"
                    >
                      <div className="flex items-center gap-4">
                        <div className="text-2xl">🔗</div>
                        <div>
                          <p className="font-medium text-white">{wh.url}</p>
                          <p className="text-xs text-muted-foreground">
                            Events: {wh.events.join(", ")}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={wh.is_active ? "default" : "destructive"}>
                          {wh.is_active ? "Active" : "Disabled"}
                        </Badge>
                        <Button variant="ghost" size="sm">
                          Test
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Documentation Tab */}
        <TabsContent value="docs" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>API Documentation</CardTitle>
              <CardDescription>
                How to use the PersonaAI API
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg bg-surface p-4">
                <h3 className="mb-2 font-medium text-white">Authentication</h3>
                <p className="text-sm text-muted-foreground">
                  Include your API key in the <code>X-API-Key</code> header:
                </p>
                <pre className="mt-2 overflow-x-auto rounded bg-black/50 p-3 text-sm text-green-400">
{`curl -H "X-API-Key: pai_your_key_here" \\
     ${API_URL}/twins`}
                </pre>
              </div>

              <div className="rounded-lg bg-surface p-4">
                <h3 className="mb-2 font-medium text-white">Rate Limits</h3>
                <p className="text-sm text-muted-foreground">
                  Default: 1,000 requests per day. Contact support for higher limits.
                </p>
              </div>

              <div className="rounded-lg bg-surface p-4">
                <h3 className="mb-2 font-medium text-white">Webhook Events</h3>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li>• <code>twin.created</code> — New twin created</li>
                  <li>• <code>twin.chat</code> — Chat message sent</li>
                  <li>• <code>source.processed</code> — Source ingestion complete</li>
                  <li>• <code>subscription.changed</code> — Plan changed</li>
                </ul>
              </div>

              <div className="rounded-lg bg-surface p-4">
                <h3 className="mb-2 font-medium text-white">Endpoints</h3>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li>• <code>GET /twins</code> — List your twins</li>
                  <li>• <code>POST /twins/{`{id}`}/chat</code> — Chat with a twin</li>
                  <li>• <code>POST /twins/{`{id}`}/voice/chat</code> — Voice chat</li>
                  <li>• <code>GET /twins/{`{id}`}/sources</code> — List sources</li>
                  <li>• <code>POST /twins/{`{id}`}/interviews</code> — Start interview</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      </div>
    </div>
    </AuthGuard>
  );
}
