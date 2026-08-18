"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { API_URL } from "@/lib/config";

interface PublicProfileProps {
  slug: string;
}

interface Twin {
  id: string;
  name: string;
  slug: string;
  tagline: string | null;
  bio: string | null;
  avatar_url: string | null;
  cover_url: string | null;
  verification_level: string;
  total_chats: number;
  avg_fidelity: number | null;
  created_at: string;
  category_name: string | null;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: any[];
}

export function PublicProfile({ slug }: PublicProfileProps) {
  const [twin, setTwin] = useState<Twin | null>(null);
  const [loading, setLoading] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchTwin();
  }, [slug]);

  useEffect(() => {
    if (showChat) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, showChat]);

  const fetchTwin = async () => {
    try {
      const res = await fetch(`${API_URL}/twins/public/${slug}`);
      if (res.ok) {
        const data = await res.json();
        setTwin(data);
      }
    } catch (error) {
      console.error("Failed to fetch twin:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || chatLoading || !twin) return;

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setChatLoading(true);

    try {
      const res = await fetch(`${API_URL}/twins/public/${slug}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.content }),
      });

      if (res.ok) {
        const data = await res.json();
        const assistantMessage: Message = {
          id: `resp-${Date.now()}`,
          role: "assistant",
          content: data.reply,
          sources: data.sources,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error("Failed to send message:", error);
    } finally {
      setChatLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getVerificationBadge = (level: string) => {
    switch (level) {
      case "official":
        return <Badge className="bg-blue-500/20 text-blue-400">✓ Official</Badge>;
      case "id_verified":
        return <Badge className="bg-green-500/20 text-green-400">✓ Verified</Badge>;
      case "email_verified":
        return <Badge className="bg-yellow-500/20 text-yellow-400">✓ Email</Badge>;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!twin) {
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center">
        <h1 className="mb-4 text-2xl font-bold text-white">Twin Not Found</h1>
        <p className="mb-4 text-muted-foreground">
          This twin doesn't exist or is not public.
        </p>
        <Link href="/directory">
          <Button>Browse Directory</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-dvh bg-background">
      {/* Hero */}
      <section className="border-b bg-gradient-to-b from-primary/10 to-background py-12">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6">
          <Avatar className="mx-auto mb-4 h-24 w-24">
            <AvatarFallback className="bg-primary/20 text-2xl text-primary">
              {twin.name.slice(0, 2).toUpperCase()}
            </AvatarFallback>
          </Avatar>

          <div className="mb-2 flex items-center justify-center gap-2">
            <h1 className="text-3xl font-bold text-white">{twin.name}</h1>
            {getVerificationBadge(twin.verification_level)}
          </div>

          {twin.tagline && (
            <p className="mb-4 text-lg text-muted-foreground">{twin.tagline}</p>
          )}

          <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
            <span>{twin.total_chats.toLocaleString()} chats</span>
            {twin.category_name && (
              <>
                <span>•</span>
                <span>{twin.category_name}</span>
              </>
            )}
            {twin.avg_fidelity && (
              <>
                <span>•</span>
                <span>{(twin.avg_fidelity * 100).toFixed(0)}% fidelity</span>
              </>
            )}
          </div>

          <Button
            className="mt-6"
            onClick={() => setShowChat(true)}
          >
            Start Conversation
          </Button>
        </div>
      </section>

      {/* Bio */}
      {twin.bio && (
        <section className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
          <Card>
            <CardContent className="p-6">
              <h2 className="mb-3 text-lg font-semibold text-white">About</h2>
              <p className="whitespace-pre-wrap text-muted-foreground">
                {twin.bio}
              </p>
            </CardContent>
          </Card>
        </section>
      )}

      {/* Chat Modal */}
      {showChat && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 sm:items-center sm:p-4">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex h-[80vh] w-full max-w-2xl flex-col rounded-t-2xl bg-background sm:rounded-2xl"
          >
            {/* Chat Header */}
            <div className="flex items-center justify-between border-b p-4">
              <div className="flex items-center gap-3">
                <Avatar>
                  <AvatarFallback className="bg-primary/20 text-primary">
                    {twin.name.slice(0, 2).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <h3 className="font-semibold text-white">{twin.name}</h3>
                  <p className="text-xs text-muted-foreground">Online</p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setShowChat(false)}>
                ✕
              </Button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4">
              {messages.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center text-center">
                  <div className="mb-4 text-4xl">💬</div>
                  <h3 className="mb-2 text-lg font-medium text-white">
                    Chat with {twin.name}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Ask anything based on their knowledge
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${
                        message.role === "user" ? "justify-end" : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          message.role === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-surface text-white"
                        }`}
                      >
                        <p className="whitespace-pre-wrap text-sm">
                          {message.content}
                        </p>
                      </div>
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="flex justify-start">
                      <div className="rounded-lg bg-surface p-3">
                        <div className="flex items-center gap-1">
                          <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground" />
                          <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:0.2s]" />
                          <div className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:0.4s]" />
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* Input */}
            <div className="border-t p-4">
              <div className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={`Ask ${twin.name}...`}
                  disabled={chatLoading}
                />
                <Button onClick={handleSend} disabled={chatLoading || !input.trim()}>
                  Send
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
