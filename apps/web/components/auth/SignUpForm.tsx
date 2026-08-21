"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Loader2, Check, X, Shield, ShieldCheck, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { GoogleButton } from "@/components/auth/GoogleButton";
import { API_URL } from "@/lib/config";

function AuthDivider() {
  return (
    <div className="relative my-4">
      <div className="absolute inset-0 flex items-center">
        <span className="w-full border-t border-white/[0.06]" />
      </div>
      <div className="relative flex justify-center text-xs">
        <span className="bg-card px-3 text-muted-foreground">OR</span>
      </div>
    </div>
  );
}

function getPasswordChecks(password: string) {
  return [
    { label: "At least 8 characters", met: password.length >= 8 },
    { label: "Contains uppercase letter", met: /[A-Z]/.test(password) },
    { label: "Contains lowercase letter", met: /[a-z]/.test(password) },
    { label: "Contains a number", met: /\d/.test(password) },
    { label: "Contains special character", met: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password) },
  ];
}

function getPasswordStrength(checks: { met: boolean }[]) {
  const score = checks.filter((c) => c.met).length;
  if (score <= 1) return { label: "Very weak", color: "text-red-500", barColor: "bg-red-500", icon: ShieldAlert, pct: 20 };
  if (score === 2) return { label: "Weak", color: "text-orange-500", barColor: "bg-orange-500", icon: ShieldAlert, pct: 40 };
  if (score === 3) return { label: "Fair", color: "text-yellow-500", barColor: "bg-yellow-500", icon: Shield, pct: 60 };
  if (score === 4) return { label: "Strong", color: "text-green-500", barColor: "bg-green-500", icon: ShieldCheck, pct: 80 };
  return { label: "Very strong", color: "text-emerald-500", barColor: "bg-emerald-500", icon: ShieldCheck, pct: 100 };
}

const suggestions = [
  "Try mixing uppercase and lowercase letters",
  "Add numbers like your birth year or a random 4-digit code",
  "Use special characters like !@#$%^&*",
  "Consider a passphrase: 3+ random words (e.g. 'Moon$tar42!')",
  "Avoid common words like 'password', '123456', or your name",
];

export function SignUpForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [focused, setFocused] = useState(false);

  const checks = useMemo(() => getPasswordChecks(password), [password]);
  const strength = useMemo(() => getPasswordStrength(checks), [checks]);
  const showHints = password.length > 0 || focused;
  const passwordsMatch = confirmPassword.length > 0 && password === confirmPassword;
  const passwordsMismatch = confirmPassword.length > 0 && password !== confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email.trim()) {
      setError("Email is required");
      return;
    }
    if (!password) {
      setError("Password is required");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (strength.pct < 60) {
      setError("Please choose a stronger password");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: email.split("@")[0] }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Signup failed");

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_id", data.user_id);
      toast.success("Account created!");
      router.push("/create");
    } catch (err: any) {
      setError(err.message || "Signup failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <GoogleButton />
      <AuthDivider />

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5">Email</label>
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
            </svg>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full bg-background border border-white/[0.06] rounded-xl pl-10 pr-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-gold-500/50 transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5">Password</label>
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
            </svg>
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder="Create a strong password"
              className="w-full bg-background border border-white/[0.06] rounded-xl pl-10 pr-10 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-gold-500/50 transition-colors"
            />
            <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>

          {showHints && password.length > 0 && (
            <div className="mt-3 space-y-2">
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-300 ${strength.barColor}`} style={{ width: `${strength.pct}%` }} />
                </div>
                <span className={`text-xs font-medium ${strength.color} flex items-center gap-1`}>
                  <strength.icon className="w-3 h-3" />
                  {strength.label}
                </span>
              </div>
              <div className="grid grid-cols-1 gap-1">
                {checks.map((check, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-xs">
                    {check.met ? (
                      <Check className="w-3 h-3 text-emerald-500" />
                    ) : (
                      <X className="w-3 h-3 text-muted-foreground/50" />
                    )}
                    <span className={check.met ? "text-emerald-500" : "text-muted-foreground"}>{check.label}</span>
                  </div>
                ))}
              </div>
              {strength.pct < 60 && (
                <div className="mt-2 rounded-lg bg-gold-500/5 border border-gold-500/10 p-2.5">
                  <p className="text-[11px] text-gold-500/80 font-medium mb-1">Password tips:</p>
                  <ul className="space-y-0.5">
                    {suggestions.slice(0, 3).map((s, i) => (
                      <li key={i} className="text-[11px] text-muted-foreground flex items-start gap-1">
                        <span className="text-gold-500/60 mt-0.5">•</span> {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1.5">Confirm Password</label>
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
            </svg>
            <input
              type={showPassword ? "text" : "password"}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              className={`w-full bg-background border rounded-xl pl-10 pr-10 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none transition-colors ${
                passwordsMismatch ? "border-red-500/50 focus:border-red-500/70" : passwordsMatch ? "border-emerald-500/50 focus:border-emerald-500/70" : "border-white/[0.06] focus:border-gold-500/50"
              }`}
            />
            {passwordsMatch && <Check className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-500" />}
            {passwordsMismatch && <X className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-red-500" />}
          </div>
          {passwordsMismatch && <p className="text-xs text-red-500 mt-1">Passwords do not match</p>}
        </div>

        {error && (
          <div className="rounded-lg bg-red-500/5 border border-red-500/10 p-3">
            <p className="text-xs text-red-500">{error}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full btn-gold py-2.5 rounded-xl text-sm font-semibold text-primary-foreground disabled:opacity-50 flex items-center justify-center gap-2 transition-all"
        >
          {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create account"}
        </button>
      </form>
    </div>
  );
}
