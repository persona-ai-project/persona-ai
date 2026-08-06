"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Loader2, ArrowLeft, Mail, CheckCircle } from "lucide-react";
import { toast } from "sonner";

import { GoogleButton } from "@/components/auth/GoogleButton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_URL } from "@/lib/config";

function AuthDivider() {
  return (
    <div className="relative">
      <div className="absolute inset-0 flex items-center">
        <span className="w-full border-t border-border/60" />
      </div>
      <div className="relative flex justify-center text-xs">
        <span className="bg-surface px-3 text-muted-foreground">
          or continue with email
        </span>
      </div>
    </div>
  );
}

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

interface FormErrors {
  email?: string;
  password?: string;
}

async function safeJsonParse(response: Response): Promise<Record<string, unknown>> {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(
      `Server error (${response.status}). Please try again later.`
    );
  }
}

type View = "login" | "forgot" | "forgot-sent";

export function LoginForm() {
  const router = useRouter();
  const [view, setView] = useState<View>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotError, setForgotError] = useState("");

  const validate = (): FormErrors => {
    const nextErrors: FormErrors = {};

    if (!email.trim()) {
      nextErrors.email = "Email is required";
    } else if (!isValidEmail(email)) {
      nextErrors.email = "Please enter a valid email address";
    }

    if (!password) {
      nextErrors.password = "Password is required";
    } else if (password.length < 8) {
      nextErrors.password = "Password must be at least 8 characters";
    }

    return nextErrors;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const nextErrors = validate();
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) return;

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await safeJsonParse(response);

      if (!response.ok) {
        throw new Error(
          (data as { detail?: string }).detail || "Invalid email or password."
        );
      }

      localStorage.setItem(
        "access_token",
        (data as { access_token: string }).access_token
      );
      localStorage.setItem("user_id", (data as { user_id: string }).user_id);

      const personaRes = await fetch(
        `${API_URL}/persona/${(data as { user_id: string }).user_id}`,
        {
          headers: {
            Authorization: `Bearer ${(data as { access_token: string }).access_token}`,
          },
        }
      );
      const persona = await personaRes.json();
      const isEmpty =
        !persona?.traits?.length &&
        !persona?.communication_style &&
        !persona?.identity?.name;

      toast.success("Logged in successfully!");
      router.push(isEmpty ? "/onboarding" : "/dashboard");
    } catch (error) {
      setIsSubmitting(false);
      toast.error(
        error instanceof Error ? error.message : "Invalid email or password."
      );
    }
  };

  const handleForgotPassword = async (event: React.FormEvent) => {
    event.preventDefault();
    setForgotError("");

    if (!forgotEmail.trim()) {
      setForgotError("Email is required");
      return;
    }
    if (!isValidEmail(forgotEmail)) {
      setForgotError("Please enter a valid email address");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_URL}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: forgotEmail }),
      });

      const data = await safeJsonParse(response);

      if (!response.ok) {
        throw new Error(
          (data as { detail?: string }).detail ||
            "Failed to send reset email. Please try again."
        );
      }

      setView("forgot-sent");
    } catch (error) {
      setForgotError(
        error instanceof Error
          ? error.message
          : "Failed to send reset email. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (view === "forgot-sent") {
    return (
      <div className="flex flex-col gap-5">
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-green-500/10">
            <CheckCircle className="size-6 text-green-500" />
          </div>
          <h2 className="text-lg font-semibold">Check your email</h2>
          <p className="text-sm text-muted-foreground">
            We sent a password reset link to{" "}
            <span className="font-medium text-foreground">{forgotEmail}</span>
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => setView("login")}
          className="h-11 w-full text-base"
        >
          <ArrowLeft className="mr-2 size-4" />
          Back to Sign In
        </Button>
      </div>
    );
  }

  if (view === "forgot") {
    return (
      <div className="flex flex-col gap-5">
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-primary/10">
            <Mail className="size-6 text-primary" />
          </div>
          <h2 className="text-lg font-semibold">Reset your password</h2>
          <p className="text-sm text-muted-foreground">
            Enter your email and we&apos;ll send you a reset link.
          </p>
        </div>

        <form
          onSubmit={handleForgotPassword}
          className="flex flex-col gap-4"
          noValidate
        >
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="forgotEmail">Email</Label>
            <Input
              id="forgotEmail"
              type="email"
              placeholder="you@example.com"
              value={forgotEmail}
              onChange={(event) => {
                setForgotEmail(event.target.value);
                setForgotError("");
              }}
              aria-invalid={!!forgotError}
              className="h-10"
            />
            {forgotError ? (
              <p className="text-xs text-red-500">{forgotError}</p>
            ) : null}
          </div>

          <Button
            type="submit"
            disabled={isSubmitting}
            className="h-11 w-full text-base"
          >
            {isSubmitting ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              "Send Reset Link"
            )}
          </Button>
        </form>

        <Button
          type="button"
          variant="ghost"
          onClick={() => setView("login")}
          className="w-full text-sm"
        >
          <ArrowLeft className="mr-2 size-4" />
          Back to Sign In
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <GoogleButton />
      <AuthDivider />

      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              if (errors.email) {
                setErrors((prev) => ({ ...prev, email: undefined }));
              }
            }}
            aria-invalid={!!errors.email}
            className="h-10"
          />
          {errors.email ? (
            <p className="text-xs text-red-500">{errors.email}</p>
          ) : null}
        </div>

        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <button
              type="button"
              onClick={() => setView("forgot")}
              className="text-xs text-primary transition-colors hover:text-primary/80"
            >
              Forgot password?
            </button>
          </div>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
                if (errors.password) {
                  setErrors((prev) => ({ ...prev, password: undefined }));
                }
              }}
              aria-invalid={!!errors.password}
              className="h-10 pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <EyeOff className="size-4" />
              ) : (
                <Eye className="size-4" />
              )}
            </button>
          </div>
          {errors.password ? (
            <p className="text-xs text-red-500">{errors.password}</p>
          ) : null}
        </div>

        <Button
          type="submit"
          disabled={isSubmitting}
          className="h-11 w-full text-base"
        >
          {isSubmitting ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            "Sign In"
          )}
        </Button>
      </form>
    </div>
  );
}
