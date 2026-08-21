"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { API_URL } from "@/lib/config";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { NavBar } from "@/components/layout/NavBar";

interface TwinChatProps {
  twinId: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: any[];
  knowledge_used?: number;
  confidence?: number;
  audio_url?: string;
}

export function TwinChat({ twinId }: TwinChatProps) {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [twinName, setTwinName] = useState("Twin");
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    fetchTwinName();
    fetchVoiceConfig();
  }, [twinId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchTwinName = async () => {
    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/twins/${twinId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setTwinName(data.name);
      }
    } catch (error) {
      console.error("Failed to fetch twin:", error);
    }
  };

  const fetchVoiceConfig = async () => {
    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/twins/${twinId}/voice/config`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setVoiceEnabled(data.voice_enabled);
      }
    } catch (error) {
      console.error("Failed to fetch voice config:", error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/twins/${twinId}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: userMessage.content,
          include_sources: true,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const assistantMessage: Message = {
          id: data.message_id || `temp-${Date.now()}`,
          role: "assistant",
          content: data.reply,
          sources: data.sources,
          knowledge_used: data.knowledge_used,
          confidence: data.confidence,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        const errorData = await res.json();
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: `Error: ${errorData.detail || "Failed to get response"}`,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: "Error: Failed to connect to the server",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: "audio/webm",
      });
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        await sendVoiceMessage(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Failed to start recording:", error);
      alert("Could not access microphone. Please check permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendVoiceMessage = async (audioBlob: Blob) => {
    setLoading(true);

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: "🎤 Voice message",
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      const token = localStorage.getItem("access_token") || "";
      const formData = new FormData();
      formData.append("file", audioBlob, "recording.webm");

      const res = await fetch(`${API_URL}/twins/${twinId}/voice/chat`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        const assistantMessage: Message = {
          id: `voice-${Date.now()}`,
          role: "assistant",
          content: data.text_response,
          audio_url: data.audio_url,
        };
        setMessages((prev) => [...prev, assistantMessage]);

        // Auto-play response audio
        if (data.audio_url) {
          playAudio(data.audio_url);
        }
      } else {
        const errorData = await res.json();
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: `Error: ${errorData.detail || "Voice chat failed"}`,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: "Error: Failed to connect to voice service",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const playAudio = (url: string) => {
    setPlayingAudio(url);
    const audio = new Audio(url);
    audio.onended = () => setPlayingAudio(null);
    audio.play().catch((err) => {
      console.error("Failed to play audio:", err);
      setPlayingAudio(null);
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <AuthGuard>
      <NavBar />
      <div className="container mx-auto py-8">
      <div className="flex h-[calc(100dvh-200px)] flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 border-b pb-4">
        <Button variant="ghost" size="sm" onClick={() => router.back()}>
          ← Back
        </Button>
        <Avatar>
          <AvatarFallback className="bg-primary/20 text-primary">
            {twinName.slice(0, 2).toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <div>
          <h1 className="font-semibold text-white">{twinName}</h1>
          <p className="text-xs text-muted-foreground">AI Digital Twin</p>
        </div>
        {voiceEnabled && (
          <div className="ml-auto flex items-center gap-2">
            <span className="text-xs text-green-400">🎤 Voice Enabled</span>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-4 text-4xl">💬</div>
            <h3 className="mb-2 text-lg font-medium text-white">
              Start a conversation
            </h3>
            <p className="text-sm text-muted-foreground">
              Ask {twinName} anything based on their knowledge
            </p>
            {voiceEnabled && (
              <p className="mt-2 text-xs text-muted-foreground">
                🎤 Voice chat available — click the microphone to speak
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-surface text-white"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Audio playback button for assistant messages */}
                  {message.role === "assistant" && message.audio_url && (
                    <div className="mt-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => playAudio(message.audio_url!)}
                        disabled={playingAudio === message.audio_url}
                        className="h-8 text-xs"
                      >
                        {playingAudio === message.audio_url ? "🔊 Playing..." : "🔊 Listen"}
                      </Button>
                    </div>
                  )}
                  
                  {message.role === "assistant" && message.sources && message.sources.length > 0 && (
                    <div className="mt-3 border-t border-white/10 pt-3">
                      <p className="mb-2 text-xs text-muted-foreground">
                        Sources used: {message.knowledge_used}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {message.sources.slice(0, 3).map((source, i) => (
                          <span
                            key={i}
                            className="rounded bg-white/10 px-2 py-1 text-xs"
                          >
                            {source.snippet?.slice(0, 50)}...
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="rounded-lg bg-surface p-4">
                  <div className="flex items-center gap-2">
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
      <div className="border-t pt-4">
        <div className="flex gap-2">
          {voiceEnabled && (
            <Button
              variant={isRecording ? "destructive" : "outline"}
              size="icon"
              onClick={isRecording ? stopRecording : startRecording}
              disabled={loading}
              className="shrink-0"
            >
              {isRecording ? "⏹️" : "🎤"}
            </Button>
          )}
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isRecording
                ? "Listening..."
                : `Ask ${twinName} something...`
            }
            disabled={loading || isRecording}
          />
          <Button onClick={handleSend} disabled={loading || !input.trim()}>
            Send
          </Button>
        </div>
      </div>
      </div>
      </div>
    </AuthGuard>
  );
}
