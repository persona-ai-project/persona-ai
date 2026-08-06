"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { API_URL, GOOGLE_CLIENT_ID } from "@/lib/config";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
          }) => void;
          renderButton: (
            parent: HTMLElement,
            config: {
              type: "standard";
              theme: string;
              size: string;
              text: string;
              shape: string;
              width: number;
            }
          ) => void;
        };
      };
    };
  }
}

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  );
}

interface GoogleButtonProps {
  className?: string;
}

export function GoogleButton({ className }: GoogleButtonProps) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const buttonContainerRef = useRef<HTMLDivElement>(null);
  const googleInitialized = useRef(false);

  const handleGoogleCredential = useCallback(
    async (response: { credential: string }) => {
      if (isLoading) return;
      setIsLoading(true);

      try {
        const res = await fetch(`${API_URL}/auth/google`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ credential: response.credential }),
        });

        const text = await res.text();
        let data: Record<string, unknown>;
        try {
          data = JSON.parse(text);
        } catch {
          throw new Error(
            `Server error (${res.status}). Please try again later.`
          );
        }

        if (!res.ok) {
          throw new Error(
            (data as { detail?: string }).detail || "Google login failed."
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

        toast.success("Logged in with Google!");
        router.push(isEmpty ? "/onboarding" : "/dashboard");
      } catch (error) {
        setIsLoading(false);
        toast.error(
          error instanceof Error ? error.message : "Google login failed."
        );
      }
    },
    [isLoading, router]
  );

  useEffect(() => {
    if (googleInitialized.current || !GOOGLE_CLIENT_ID) return;

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      setScriptLoaded(true);
      if (window.google?.accounts?.id) {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleCredential,
        });
        googleInitialized.current = true;

        if (buttonContainerRef.current) {
          window.google.accounts.id.renderButton(
            buttonContainerRef.current,
            {
              type: "standard",
              theme: "outline",
              size: "large",
              text: "continue_with",
              shape: "rectangular",
              width: buttonContainerRef.current.offsetWidth || 380,
            }
          );
        }
      }
    };
    document.head.appendChild(script);

    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, [handleGoogleCredential]);

  if (!GOOGLE_CLIENT_ID) {
    return null;
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <div ref={buttonContainerRef} className="w-full" />
      {!scriptLoaded && (
        <Button
          type="button"
          variant="outline"
          disabled
          className={cn(
            "h-11 w-full border-primary/50 bg-surface text-foreground hover:bg-surface hover:border-primary",
            className
          )}
        >
          {isLoading ? (
            <Loader2 className="size-5 animate-spin text-primary" />
          ) : (
            <GoogleIcon />
          )}
          Continue with Google
        </Button>
      )}
    </div>
  );
}
