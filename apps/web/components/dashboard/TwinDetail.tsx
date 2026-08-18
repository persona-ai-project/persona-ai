"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { API_URL } from "@/lib/config";

interface TwinDetailProps {
  twinId: string;
}

interface Twin {
  id: string;
  name: string;
  slug: string;
  tagline: string | null;
  bio: string | null;
  status: string;
  visibility: string;
  verification_level: string;
  total_chats: number;
  total_messages: number;
  avg_fidelity: number | null;
  created_at: string;
  category_name: string | null;
  knowledge_stats: Record<string, number>;
  source_stats: Record<string, number>;
  interview_stats: Record<string, number>;
}

interface Source {
  id: string;
  source_type: string;
  title: string | null;
  status: string;
  chunk_count: number;
  created_at: string;
}

interface Interview {
  id: string;
  topic: string | null;
  topic_name: string | null;
  status: string;
  questions_asked: number;
  items_extracted: number;
  created_at: string;
}

export function TwinDetail({ twinId }: TwinDetailProps) {
  const router = useRouter();
  const [twin, setTwin] = useState<Twin | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTwin();
    fetchSources();
    fetchInterviews();
  }, [twinId]);

  const fetchTwin = async () => {
    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/twins/${twinId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setTwin(data);
      }
    } catch (error) {
      console.error("Failed to fetch twin:", error);
    }
  };

  const fetchSources = async () => {
    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/twins/${twinId}/sources?limit=50`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSources(data.sources || []);
      }
    } catch (error) {
      console.error("Failed to fetch sources:", error);
    }
  };

  const fetchInterviews = async () => {
    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/twins/${twinId}/interviews?limit=50`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setInterviews(data.sessions || []);
      }
    } catch (error) {
      console.error("Failed to fetch interviews:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "bg-green-500/20 text-green-400";
      case "draft": return "bg-yellow-500/20 text-yellow-400";
      case "processing": return "bg-blue-500/20 text-blue-400";
      case "ready": return "bg-green-500/20 text-green-400";
      case "failed": return "bg-red-500/20 text-red-400";
      case "completed": return "bg-purple-500/20 text-purple-400";
      default: return "bg-gray-500/20 text-gray-400";
    }
  };

  const getTotalKnowledge = () => {
    if (!twin?.knowledge_stats) return 0;
    return Object.values(twin.knowledge_stats).reduce((a, b) => a + b, 0);
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!twin) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center">
        <p className="text-muted-foreground">Twin not found</p>
        <Button variant="link" onClick={() => router.push("/dashboard")}>
          Back to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarFallback className="bg-primary/20 text-xl text-primary">
              {twin.name.slice(0, 2).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div>
            <h1 className="text-2xl font-bold text-white">{twin.name}</h1>
            {twin.tagline && (
              <p className="text-muted-foreground">{twin.tagline}</p>
            )}
            <div className="mt-2 flex items-center gap-2">
              <Badge className={getStatusColor(twin.status)}>{twin.status}</Badge>
              <Badge variant="outline">{twin.visibility}</Badge>
              {twin.category_name && (
                <Badge variant="secondary">{twin.category_name}</Badge>
              )}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => router.push(`/twins/${twinId}/chat`)}
          >
            Chat
          </Button>
          <Button
            onClick={() => router.push(`/twins/${twinId}/settings`)}
          >
            Settings
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-muted-foreground">Total Chats</p>
            <p className="text-2xl font-bold text-white">{twin.total_chats}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-muted-foreground">Messages</p>
            <p className="text-2xl font-bold text-white">{twin.total_messages}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-muted-foreground">Knowledge Items</p>
            <p className="text-2xl font-bold text-white">{getTotalKnowledge()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-muted-foreground">Sources</p>
            <p className="text-2xl font-bold text-white">{sources.length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="sources" className="w-full">
        <TabsList>
          <TabsTrigger value="sources">Sources ({sources.length})</TabsTrigger>
          <TabsTrigger value="knowledge">Knowledge ({getTotalKnowledge()})</TabsTrigger>
          <TabsTrigger value="interviews">Interviews ({interviews.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="sources" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Sources</CardTitle>
              <Button size="sm" onClick={() => router.push(`/twins/${twinId}/sources`)}>
                + Add Source
              </Button>
            </CardHeader>
            <CardContent>
              {sources.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  No sources yet. Add documents, URLs, or WhatsApp exports to build knowledge.
                </p>
              ) : (
                <div className="space-y-3">
                  {sources.map((source) => (
                    <div
                      key={source.id}
                      className="flex items-center justify-between rounded-lg border p-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="text-2xl">
                          {source.source_type === "url" ? "🔗" : "📄"}
                        </div>
                        <div>
                          <p className="font-medium text-white">
                            {source.title || "Untitled"}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {source.source_type} • {source.chunk_count} chunks
                          </p>
                        </div>
                      </div>
                      <Badge className={getStatusColor(source.status)}>
                        {source.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="knowledge" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Knowledge Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(twin.knowledge_stats || {}).length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  No knowledge items yet. Start an interview or upload sources to build knowledge.
                </p>
              ) : (
                <div className="space-y-3">
                  {Object.entries(twin.knowledge_stats || {}).map(([type, count]) => (
                    <div
                      key={type}
                      className="flex items-center justify-between rounded-lg border p-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="text-2xl">
                          {type === "fact" ? "📝" :
                           type === "opinion" ? "💬" :
                           type === "preference" ? "❤️" :
                           type === "memory" ? "🧠" :
                           type === "skill" ? "⚡" :
                           type === "relationship" ? "👥" :
                           type === "event" ? "📅" : "📦"}
                        </div>
                        <div>
                          <p className="font-medium text-white capitalize">{type}</p>
                        </div>
                      </div>
                      <span className="text-2xl font-bold text-white">{count}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="interviews" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Interview Sessions</CardTitle>
              <Button size="sm" onClick={() => router.push(`/twins/${twinId}/interviews`)}>
                + Start Interview
              </Button>
            </CardHeader>
            <CardContent>
              {interviews.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  No interviews yet. Start an interview to extract knowledge through conversation.
                </p>
              ) : (
                <div className="space-y-3">
                  {interviews.map((interview) => (
                    <div
                      key={interview.id}
                      className="flex items-center justify-between rounded-lg border p-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="text-2xl">🎤</div>
                        <div>
                          <p className="font-medium text-white">
                            {interview.topic_name || "General"}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {interview.questions_asked} questions • {interview.items_extracted} items extracted
                          </p>
                        </div>
                      </div>
                      <Badge className={getStatusColor(interview.status)}>
                        {interview.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
