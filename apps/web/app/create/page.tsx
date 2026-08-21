"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { API_URL } from "@/lib/config";

const ACCENT_COLORS = [
  { name: "gold", class: "bg-gold-500" },
  { name: "purple", class: "bg-twin-purple" },
  { name: "blue", class: "bg-twin-blue" },
  { name: "green", class: "bg-twin-green" },
  { name: "pink", class: "bg-twin-pink" },
];

export default function CreateTwinPage() {
  const router = useRouter();
  const [step, setStep] = useState<1 | 2>(1);
  const [loading, setLoading] = useState(false);

  // Step 1: Identity
  const [fullName, setFullName] = useState("");
  const [tagline, setTagline] = useState("");
  const [role, setRole] = useState("");
  const [bio, setBio] = useState("");
  const [expertise, setExpertise] = useState<string[]>([]);
  const [expertiseInput, setExpertiseInput] = useState("");
  const [accentColor, setAccentColor] = useState("gold");
  const [isPublic, setIsPublic] = useState(true);

  // Step 2: Interview
  const [twinId, setTwinId] = useState<string | null>(null);
  const [interviewStarted, setInterviewStarted] = useState(false);

  const addExpertise = () => {
    if (expertiseInput.trim() && !expertise.includes(expertiseInput.trim())) {
      setExpertise([...expertise, expertiseInput.trim()]);
      setExpertiseInput("");
    }
  };

  const removeExpertise = (skill: string) => {
    setExpertise(expertise.filter((s) => s !== skill));
  };

  const handleContinueToInterview = async () => {
    if (!fullName.trim()) return;
    setLoading(true);
    try {
      const token = localStorage.getItem("access_token") || "";
      const res = await fetch(`${API_URL}/twins`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: fullName,
          tagline: tagline || undefined,
          role: role || undefined,
          bio: bio || undefined,
          expertise,
          accent_color: accentColor,
          is_public: isPublic,
          twin_type: "owner",
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setTwinId(data.id);
        setStep(2);
      } else {
        const err = await res.json();
        alert(err.detail || "Failed to create twin");
      }
    } catch (e) {
      console.error("Failed to create twin:", e);
    } finally {
      setLoading(false);
    }
  };

  const startInterview = () => {
    if (twinId) {
      router.push(`/onboarding?twinId=${twinId}&name=${encodeURIComponent(fullName)}`);
    }
  };

  return (
    <div className="p-6 lg:p-8 max-w-2xl mx-auto">
      {/* Stepper */}
      <div className="flex items-center justify-center gap-3 mb-8">
        <div className={`flex items-center gap-2 ${step === 1 ? "text-gold-500" : "text-muted-foreground"}`}>
          <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step === 1 ? "bg-gold-500 text-primary-foreground" : "bg-gold-500/20 text-gold-500"}`}>
            1
          </span>
          <span className="text-sm font-medium">Identity</span>
        </div>
        <div className="w-8 h-px bg-white/10" />
        <div className={`flex items-center gap-2 ${step === 2 ? "text-gold-500" : "text-muted-foreground"}`}>
          <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step === 2 ? "bg-gold-500 text-primary-foreground" : "bg-white/10 text-muted-foreground"}`}>
            2
          </span>
          <span className="text-sm font-medium">Interview</span>
        </div>
      </div>

      {step === 1 ? (
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
          <h1 className="text-2xl font-bold text-foreground mb-1">Create a digital twin</h1>
          <p className="text-muted-foreground text-sm mb-8">Define who this twin represents. The interview comes next.</p>

          <div className="space-y-5">
            {/* Full Name */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Full name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Sareem Gauri"
                className="w-full bg-card border border-white/[0.06] rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-gold-500/50 transition-colors"
              />
            </div>

            {/* Tagline */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Tagline</label>
              <input
                type="text"
                value={tagline}
                onChange={(e) => setTagline(e.target.value)}
                placeholder="e.g. Founder · 3 startups · angel investor"
                className="w-full bg-card border border-white/[0.06] rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-gold-500/50 transition-colors"
              />
            </div>

            {/* Role */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Role</label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="Founder"
                className="w-full bg-card border border-white/[0.06] rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-gold-500/50 transition-colors"
              />
            </div>

            {/* Short Bio */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Short bio</label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="A sentence or two about their background and perspective..."
                rows={3}
                className="w-full bg-card border border-white/[0.06] rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-gold-500/50 transition-colors resize-none"
              />
            </div>

            {/* Expertise */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Expertise</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={expertiseInput}
                  onChange={(e) => setExpertiseInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addExpertise())}
                  placeholder="Add an area (e.g. Go-to-market)"
                  className="flex-1 bg-card border border-white/[0.06] rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-gold-500/50 transition-colors"
                />
                <button
                  type="button"
                  onClick={addExpertise}
                  className="px-4 py-3 rounded-xl bg-white/5 text-sm font-medium text-foreground hover:bg-white/10 transition-colors border border-white/[0.06]"
                >
                  Add
                </button>
              </div>
              {expertise.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {expertise.map((skill) => (
                    <span key={skill} className="tag flex items-center gap-1.5">
                      {skill}
                      <button onClick={() => removeExpertise(skill)} className="text-white/40 hover:text-white/80">
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Accent Color */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Accent color</label>
              <div className="flex gap-2">
                {ACCENT_COLORS.map((color) => (
                  <button
                    key={color.name}
                    onClick={() => setAccentColor(color.name)}
                    className={`w-8 h-8 rounded-full ${color.class} transition-all ${
                      accentColor === color.name ? "ring-2 ring-offset-2 ring-offset-background ring-white/40 scale-110" : "opacity-60 hover:opacity-100"
                    }`}
                  />
                ))}
              </div>
            </div>

            {/* Public Toggle */}
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                className="w-4 h-4 rounded border-white/20 bg-card text-gold-500 focus:ring-gold-500"
              />
              <span className="text-sm text-foreground">Make this twin discoverable in the public directory</span>
            </label>
          </div>

          {/* Continue Button */}
          <button
            onClick={handleContinueToInterview}
            disabled={!fullName.trim() || loading}
            className="w-full mt-8 btn-gold py-3 rounded-xl text-sm font-semibold text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                Continue to interview
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
              </>
            )}
          </button>
        </motion.div>
      ) : (
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="text-center py-12">
          {/* Mic Icon */}
          <div className="w-16 h-16 rounded-2xl bg-gold-500/10 flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
            </svg>
          </div>

          <h2 className="text-2xl font-bold text-foreground mb-2">
            Let&apos;s build {fullName}&apos;s twin
          </h2>
          <p className="text-muted-foreground max-w-md mx-auto mb-8">
            A 10-question conversational interview — about 10 minutes. Speak or type your answers. Your twin learns from each one.
          </p>

          <button
            onClick={startInterview}
            className="btn-gold inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold text-primary-foreground"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
            </svg>
            Start the interview
          </button>
        </motion.div>
      )}
    </div>
  );
}
