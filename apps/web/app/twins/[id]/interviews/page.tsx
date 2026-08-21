"use client";

import { useState, useEffect, useRef } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { NavBar } from "@/components/layout/NavBar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { API_URL } from "@/lib/config";

const TOPICS = ["background", "personality", "opinions", "skills", "relationships", "interests", "challenges", "goals"];

export default function TwinInterviewsPage({ params }: { params: { id: string } }) {
  const id = params.id;
  const [sessions, setSessions] = useState<any[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [topic, setTopic] = useState("skills");
  const messagesEnd = useRef<HTMLDivElement>(null);

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const headers = { Authorization: `Bearer ${token}` };

  const loadSessions = () => {
    if (!token) return;
    fetch(`${API_URL}/twins/${id}/interviews`, { headers })
      .then((r) => r.json())
      .then((data) => setSessions(Array.isArray(data) ? data : data.sessions || []));
  };

  useEffect(() => { loadSessions(); }, [id]);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startInterview = async () => {
    const r = await fetch(`${API_URL}/twins/${id}/interviews`, {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ topic }),
    });
    if (r.ok) {
      const data = await r.json();
      setActiveSession(data.id);
      setMessages([]);
      loadSessions();
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !activeSession || sending) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setSending(true);

    try {
      const r = await fetch(`${API_URL}/twins/${id}/interviews/${activeSession}/message`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });
      if (r.ok) {
        const data = await r.json();
        setMessages((prev) => [...prev, { role: "assistant", content: data.follow_up || data.content || "Thanks for sharing!" }]);
      }
    } catch {}
    setSending(false);
  };

  return (
    <AuthGuard>
      <NavBar />
      <div className="container mx-auto py-8 max-w-3xl">
        <h1 className="text-2xl font-bold text-white mb-6">Interviews</h1>

        {!activeSession ? (
          <>
            <Card className="mb-6">
              <CardHeader><CardTitle>Start New Interview</CardTitle></CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  <select
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {TOPICS.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
                  </select>
                  <Button onClick={startInterview}>Start Interview</Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Past Sessions</CardTitle></CardHeader>
              <CardContent>
                {sessions.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No interviews yet</p>
                ) : (
                  <div className="space-y-3">
                    {sessions.map((s) => (
                      <div key={s.id} className="flex items-center justify-between rounded-lg border p-3">
                        <div>
                          <p className="font-medium text-white">{s.topic || "General"}</p>
                          <p className="text-xs text-muted-foreground">{s.messages_count || 0} messages</p>
                        </div>
                        <Button variant="outline" size="sm" onClick={async () => {
                          setActiveSession(s.id);
                          setMessages([]);
                          try {
                            const res = await fetch(`${API_URL}/twins/${id}/interviews/${s.id}`, { headers });
                            if (res.ok) {
                              const data = await res.json();
                              const loaded = (data.messages || []).map((m: any) => ({
                                role: m.role === "interviewer" ? "assistant" : "user",
                                content: m.content,
                              }));
                              setMessages(loaded);
                            }
                          } catch {}
                        }}>
                          Resume
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        ) : (
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Interview in Progress</CardTitle>
              <Button variant="outline" size="sm" onClick={() => { setActiveSession(null); loadSessions(); }}>
                End Interview
              </Button>
            </CardHeader>
            <CardContent>
              <div className="h-96 overflow-y-auto mb-4 space-y-3">
                {messages.length === 0 && (
                  <p className="text-muted-foreground text-center py-8">Start by telling me about yourself...</p>
                )}
                {messages.map((m, i) => (
                  <div key={i} className={`rounded-lg p-3 ${m.role === "user" ? "bg-primary/10 ml-12" : "bg-muted mr-12"}`}>
                    <p className="text-sm text-white whitespace-pre-wrap">{m.content}</p>
                  </div>
                ))}
                <div ref={messagesEnd} />
              </div>
              <div className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Type your answer..."
                  disabled={sending}
                />
                <Button onClick={sendMessage} disabled={sending || !input.trim()}>
                  {sending ? "..." : "Send"}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AuthGuard>
  );
}
