"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { API_URL } from "@/lib/config";

interface Message {
  role: "interviewer" | "interviewee";
  content: string;
  timestamp: number;
}

interface InterviewState {
  sessionId: string | null;
  twinId: string | null;
  messages: Message[];
  isTyping: boolean;
  isRecording: boolean;
  phase: "welcome" | "interview" | "creating" | "done";
  twinName: string;
  error: string | null;
  currentTopic: string;
  topicExchangeCount: number;
}

const TOPIC_PROGRESSION = ["background", "personality", "skills", "goals"];

export default function InterviewOnboarding() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [state, setState] = useState<InterviewState>({
    sessionId: null,
    twinId: null,
    messages: [],
    isTyping: false,
    isRecording: false,
    phase: "welcome",
    twinName: "",
    error: null,
    currentTopic: TOPIC_PROGRESSION[0],
    topicExchangeCount: 0,
  });
  const [inputText, setInputText] = useState("");
  const [cameraActive, setCameraActive] = useState(false);
  const [micActive, setMicActive] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [state.messages, state.isTyping, scrollToBottom]);

  // Re-attach camera stream when video element mounts or camera state changes
  useEffect(() => {
    if (cameraActive && streamRef.current && videoRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [cameraActive, state.phase]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
      window.speechSynthesis?.cancel();
    };
  }, []);

  // Speak text using browser TTS
  const speakText = (text: string) => {
    if (!voiceEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    // Try to pick a natural-sounding voice
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(
      (v) => v.lang.startsWith("en") && v.name.includes("Google")
    ) || voices.find((v) => v.lang.startsWith("en"));
    if (preferred) utterance.voice = preferred;
    window.speechSynthesis.speak(utterance);
  };

  const getToken = () => localStorage.getItem("access_token");

  const apiCall = async (
    path: string,
    options: RequestInit = {}
  ): Promise<any> => {
    const token = getToken();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    if (!options.body || !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }
    const res = await fetch(`${API_URL}${path}`, { ...options, headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraActive(true);
    } catch (e) {
      console.log("Camera not available:", e);
      setCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((t) => t.stop());
        setMicActive(false);
        setState((s) => ({ ...s, isRecording: false }));
        await handleVoiceInput(blob);
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setMicActive(true);
      setState((s) => ({ ...s, isRecording: true }));
    } catch (e) {
      console.log("Mic not available:", e);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
  };

  const handleVoiceInput = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append("file", audioBlob, "recording.webm");
      const result = await fetch(`${API_URL}/voice/transcribe`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        body: formData,
      }).then((r) => {
        if (!r.ok) throw new Error("Transcription failed");
        return r.json();
      });

      if (result.text && result.text.trim()) {
        await sendMessage(result.text.trim());
      }
    } catch (e) {
      console.error("Transcription failed, falling back to text:", e);
      setState((s) => ({
        ...s,
        error: "Voice transcription unavailable. Please type your answer.",
      }));
      setTimeout(() => setState((s) => ({ ...s, error: null })), 3000);
    }
  };

  const createTwin = async (name: string): Promise<string> => {
    const result = await apiCall("/twins", {
      method: "POST",
      body: JSON.stringify({
        name,
        tagline: "Created through AI interview",
        twin_type: "owner",
      }),
    });
    return result.id;
  };

  const startInterview = async (twinId: string, personName: string, topic: string = "background"): Promise<string> => {
    const result = await apiCall(`/twins/${twinId}/interviews`, {
      method: "POST",
      body: JSON.stringify({ topic, person_name: personName || undefined }),
    });
    return result.id;
  };

  const sendMessage = async (content: string) => {
    if (!content.trim() || state.isTyping) return;

    const userMsg: Message = {
      role: "interviewee",
      content: content.trim(),
      timestamp: Date.now(),
    };

    setState((s) => ({
      ...s,
      messages: [...s.messages, userMsg],
      isTyping: true,
      error: null,
    }));
    setInputText("");

    try {
      const { sessionId, twinId } = state;

      if (!sessionId || !twinId) {
        setState((s) => ({
          ...s,
          isTyping: false,
          error: "Interview not initialized. Please refresh and try again.",
        }));
        return;
      }

      // Send message to interview
      const result = await apiCall(
        `/twins/${twinId}/interviews/${sessionId}/message`,
        {
          method: "POST",
          body: JSON.stringify({ message: content.trim() }),
        }
      );

      // The backend returns follow_up (next question) and content (echo of user msg)
      const followUp = result.follow_up || result.content;
      if (followUp) {
        const interviewerMsg: Message = {
          role: "interviewer",
          content: followUp,
          timestamp: Date.now(),
        };
        setState((s) => ({
          ...s,
          messages: [...s.messages, interviewerMsg],
          isTyping: false,
        }));

        // Speak the follow-up with TTS
        speakText(followUp);
      } else {
        setState((s) => ({
          ...s,
          isTyping: false,
        }));
      }

      // Check if interview is complete
      if (result.is_complete) {
        setState((s) => ({ ...s, phase: "creating" }));
        setTimeout(() => {
          setState((s) => ({ ...s, phase: "done" }));
        }, 3000);
        return;
      }

      // Topic progression: after 4 exchanges, move to next topic
      setState((s) => {
        const newCount = s.topicExchangeCount + 1;
        if (newCount >= 4) {
          const currentIdx = TOPIC_PROGRESSION.indexOf(s.currentTopic);
          const nextTopic = TOPIC_PROGRESSION[currentIdx + 1];
          if (nextTopic && s.twinId) {
            // Start new session with next topic in background
            startInterview(s.twinId, s.twinName, nextTopic).then((newSessionId) => {
              setState((s2) => ({
                ...s2,
                sessionId: newSessionId,
                currentTopic: nextTopic,
                topicExchangeCount: 0,
              }));
            }).catch(console.error);
            return { ...s, topicExchangeCount: 0, currentTopic: nextTopic };
          }
        }
        return { ...s, topicExchangeCount: newCount };
      });
    } catch (e: any) {
      console.error("Interview error:", e);
      setState((s) => ({
        ...s,
        isTyping: false,
        error: e.message || "Something went wrong. Please try again.",
      }));
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (inputText.trim() && !state.isTyping) {
        sendMessage(inputText);
      }
    }
  };

  const startInterviewFlow = async () => {
    const preselectedTwinId = searchParams.get("twinId");
    const preselectedName = searchParams.get("name");
    const name = state.twinName || preselectedName || "My Digital Twin";

    setState((s) => ({
      ...s,
      twinName: name,
      phase: "interview",
      isTyping: true,
    }));

    try {
      let twinId: string;
      let sessionId: string;

      if (preselectedTwinId) {
        // Twin was already created (from /create page) — just start interview
        twinId = preselectedTwinId;
        sessionId = await startInterview(twinId, name, TOPIC_PROGRESSION[0]);
      } else {
        // Create twin fresh
        twinId = await createTwin(name);
        sessionId = await startInterview(twinId, name, TOPIC_PROGRESSION[0]);
      }

      // Fetch the opening question from the interview session
      const session = await apiCall(
        `/twins/${twinId}/interviews/${sessionId}`
      );

      // Get the first interviewer message from session history
      const messages = session.messages || [];
      const openingMsg = messages.find(
        (m: any) => m.role === "interviewer"
      );

      setState((s) => ({
        ...s,
        sessionId,
        twinId,
        isTyping: false,
        messages: openingMsg
          ? [
              {
                role: "interviewer" as const,
                content: openingMsg.content,
                timestamp: Date.now(),
              },
            ]
          : [
              {
                role: "interviewer" as const,
                content: `Hey! I'm here to get to know you so I can build your digital twin. Let's start with something easy — what's your name, and what do you do?`,
                timestamp: Date.now(),
              },
            ],
      }));
    } catch (e: any) {
      console.error("Failed to start interview:", e);
      // Still show the interview with fallback welcome
      setState((s) => ({
        ...s,
        isTyping: false,
        messages: [
          {
            role: "interviewer",
            content: `Hey! I'm here to get to know you so I can build your digital twin. Let's start with something easy — what's your name, and what do you do?`,
            timestamp: Date.now(),
          },
        ],
      }));
    }
  };

  // ── Welcome Phase ──────────────────────────────────────────────────────────
  if (state.phase === "welcome") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#09090b] px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-lg w-full text-center"
        >
          {/* Camera preview */}
          <div className="mb-8 relative">
            <div className="w-48 h-48 mx-auto rounded-full overflow-hidden border-4 border-[#f59e0b]/30 bg-[#18181b]">
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="w-full h-full object-cover"
                style={{ transform: "scaleX(-1)" }}
              />
              {!cameraActive && (
                <div className="w-full h-full flex items-center justify-center text-6xl">
                  👤
                </div>
              )}
            </div>
            <button
              onClick={cameraActive ? stopCamera : startCamera}
              className="absolute bottom-2 right-[calc(50%-120px)] bg-[#f59e0b] hover:bg-[#fbbf24] text-[#09090b] rounded-full p-2 transition-colors"
            >
              {cameraActive ? "📹" : "📷"}
            </button>
          </div>

          <h1 className="text-3xl font-bold text-[#fafafa] mb-3">
            Build Your Digital Twin
          </h1>
          <p className="text-[#a1a1aa] text-lg mb-8">
            Have a quick conversation with me. I&apos;ll ask you some questions
            to capture your personality, expertise, and communication style.
          </p>

          <div className="mb-6">
            <label className="block text-sm text-[#a1a1aa] mb-2 text-left">
              What should we call your twin?
            </label>
            <input
              type="text"
              value={state.twinName}
              onChange={(e) =>
                setState((s) => ({ ...s, twinName: e.target.value }))
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") startInterviewFlow();
              }}
              placeholder="e.g. Sarah, Founder Twin, etc."
              className="w-full bg-[#27272a] border border-white/10 rounded-xl px-4 py-3 text-[#fafafa] placeholder:text-white/30 focus:outline-none focus:border-[#f59e0b] transition-colors"
            />
          </div>

          <button
            onClick={startInterviewFlow}
            className="w-full btn-gold font-semibold py-3 px-6 rounded-xl text-[#09090b]"
          >
            Start Conversation
          </button>

          <p className="text-white/40 text-sm mt-4">
            ~15-30 min · Voice or text · Camera optional
          </p>
        </motion.div>
      </div>
    );
  }

  // ── Creating / Done Phase ──────────────────────────────────────────────────
  if (state.phase === "creating" || state.phase === "done") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#09090b] px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          {state.phase === "creating" ? (
            <>
              <div className="w-16 h-16 border-4 border-[#f59e0b] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-[#fafafa] mb-2">
                Building your twin...
              </h2>
              <p className="text-[#a1a1aa]">
                Extracting personality traits and knowledge from our conversation
              </p>
            </>
          ) : (
            <>
              <div className="text-6xl mb-4">✨</div>
              <h2 className="text-2xl font-bold text-[#fafafa] mb-2">
                Your twin is ready!
              </h2>
              <p className="text-[#a1a1aa] mb-8">
                {state.twinName} has been created with{" "}
                {state.messages.filter((m) => m.role === "interviewee").length}{" "}
                insights from our conversation.
              </p>
              <div className="flex gap-4 justify-center">
                <button
                  onClick={() => router.push(`/twins/${state.twinId}/chat`)}
                  className="btn-gold font-semibold py-3 px-6 rounded-xl text-[#09090b]"
                >
                  Chat with {state.twinName}
                </button>
                <button
                  onClick={() => router.push("/dashboard")}
                  className="bg-white/10 hover:bg-white/15 text-[#fafafa] font-semibold py-3 px-6 rounded-xl transition-all"
                >
                  Dashboard
                </button>
              </div>
            </>
          )}
        </motion.div>
      </div>
    );
  }

  // ── Interview Phase ────────────────────────────────────────────────────────
  return (
    <div className="h-screen flex flex-col bg-[#09090b]">
      {/* Header */}
      <div className="border-b border-white/8 bg-[#18181b]/80 backdrop-blur-sm px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[#f59e0b]/10 flex items-center justify-center text-[#f59e0b] text-lg">
            🤖
          </div>
          <div>
            <h3 className="text-[#fafafa] font-medium text-sm">
              AI Interviewer
            </h3>
            <p className="text-[#a1a1aa] text-xs">
              Building {state.twinName || "your twin"} · {state.messages.length} messages
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setVoiceEnabled((v) => !v);
              if (voiceEnabled) window.speechSynthesis?.cancel();
            }}
            className={`p-2 rounded-lg transition-colors ${
              voiceEnabled
                ? "bg-[#f59e0b] text-[#09090b]"
                : "bg-white/5 text-white/50 hover:bg-white/10"
            }`}
            title={voiceEnabled ? "Voice ON" : "Voice OFF"}
          >
            {voiceEnabled ? "🔊" : "🔇"}
          </button>
          <button
            onClick={cameraActive ? stopCamera : startCamera}
            className={`p-2 rounded-lg transition-colors ${
              cameraActive
                ? "bg-[#f59e0b] text-[#09090b]"
                : "bg-white/5 text-white/50 hover:bg-white/10"
            }`}
          >
            {cameraActive ? "📹" : "📷"}
          </button>
          <button
            onClick={() => {
              stopCamera();
              window.speechSynthesis?.cancel();
              router.push("/dashboard");
            }}
            className="p-2 rounded-lg bg-white/5 text-white/50 hover:bg-white/10 transition-colors text-sm"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Camera strip — always rendered when active, even if phase changes */}
      {cameraActive && (
        <div className="h-32 bg-black flex justify-center shrink-0">
          <video
            ref={videoRef}
            autoPlay
            muted
            playsInline
            className="h-full object-cover"
            style={{ transform: "scaleX(-1)" }}
          />
        </div>
      )}

      {/* Error banner */}
      {state.error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm px-4 py-2 text-center shrink-0">
          {state.error}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 min-h-0">
        <AnimatePresence>
          {state.messages.map((msg, i) => (
            <motion.div
              key={`${i}-${msg.timestamp}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${
                msg.role === "interviewee" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  msg.role === "interviewee"
                    ? "bg-[#f59e0b] text-[#09090b] rounded-br-md"
                    : "bg-[#27272a] text-[#fafafa] border border-white/8 rounded-bl-md"
                }`}
              >
                {msg.role === "interviewer" && (
                  <div className="text-[#f59e0b] text-xs font-medium mb-1">
                    AI Interviewer
                  </div>
                )}
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {state.isTyping && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="bg-[#27272a] border border-white/8 rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-[#f59e0b] rounded-full animate-bounce" />
                <div
                  className="w-2 h-2 bg-[#f59e0b] rounded-full animate-bounce"
                  style={{ animationDelay: "0.1s" }}
                />
                <div
                  className="w-2 h-2 bg-[#f59e0b] rounded-full animate-bounce"
                  style={{ animationDelay: "0.2s" }}
                />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-white/8 bg-[#18181b]/80 backdrop-blur-sm px-4 py-3 shrink-0">
        <div className="flex items-end gap-2">
          <button
            onClick={micActive ? stopRecording : startRecording}
            disabled={state.isTyping}
            className={`p-3 rounded-xl transition-all shrink-0 ${
              micActive
                ? "bg-red-500 text-white animate-pulse"
                : state.isTyping
                ? "bg-white/5 text-white/20 cursor-not-allowed"
                : "bg-white/5 text-white/50 hover:bg-white/10"
            }`}
          >
            {micActive ? "⏹" : "🎤"}
          </button>
          <div className="flex-1 relative">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                state.isTyping
                  ? "Waiting for response..."
                  : "Type your answer..."
              }
              disabled={state.isTyping}
              rows={1}
              className="w-full bg-[#27272a] border border-white/10 rounded-xl px-4 py-3 text-[#fafafa] placeholder:text-white/30 focus:outline-none focus:border-[#f59e0b] resize-none transition-colors disabled:opacity-50"
              style={{ minHeight: "44px", maxHeight: "120px" }}
            />
          </div>
          <button
            onClick={() => {
              if (inputText.trim() && !state.isTyping) {
                sendMessage(inputText);
              }
            }}
            disabled={!inputText.trim() || state.isTyping}
            className="p-3 rounded-xl bg-[#f59e0b] hover:bg-[#fbbf24] disabled:bg-white/10 disabled:text-white/30 text-[#09090b] transition-all font-bold shrink-0"
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}
