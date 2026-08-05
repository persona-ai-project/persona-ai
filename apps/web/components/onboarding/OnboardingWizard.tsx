"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion, useMotionValue, useTransform, animate } from "framer-motion";
import { Check } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/chat", label: "Chat" },
  { href: "/onboarding", label: "Onboarding" },
] as const;

const TOTAL_STEPS = 5;

function PersonaAILogo() {
  return (
    <h1 className="text-xl font-semibold tracking-tight text-primary sm:text-2xl">
      PersonaAI
    </h1>
  );
}

function ProgressDots({ currentStep }: { currentStep: number }) {
  return (
    <div className="flex items-center justify-center gap-2">
      {Array.from({ length: TOTAL_STEPS }).map((_, index) => (
        <div
          key={index}
          className={cn(
            "h-2 w-2 rounded-full transition-all duration-300",
            index === currentStep
              ? "w-6 bg-primary"
              : index < currentStep
                ? "bg-primary/60"
                : "bg-muted-foreground/30"
          )}
        />
      ))}
    </div>
  );
}

function CompletenessRing({ percentage }: { percentage: number }) {
  const size = 120;
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  const count = useMotionValue(0);
  const [displayCount, setDisplayCount] = useState(0);
  const strokeOffset = useTransform(
    count,
    (value) => circumference - (value / 100) * circumference
  );

  useEffect(() => {
    const controls = animate(count, percentage, {
      duration: 1.5,
      ease: "easeOut",
      onUpdate: (latest) => setDisplayCount(Math.round(latest)),
    });
    return controls.stop;
  }, [count, percentage]);

  return (
    <div className="relative flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth={strokeWidth}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#8b5cf6"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          style={{ strokeDashoffset: strokeOffset }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-foreground">{displayCount}</span>
        <span className="text-xs text-muted-foreground">% complete</span>
      </div>
    </div>
  );
}

function QuestionStep({
  currentStep,
  question,
  value,
  onChange,
  onNext,
  isLast,
  isSubmitting,
}: {
  currentStep: number;
  question: string;
  value: string;
  onChange: (value: string) => void;
  onNext: () => void;
  isLast: boolean;
  isSubmitting: boolean;
}) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext();
  };

  return (
    <motion.div
      key="question"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.35, ease: "easeInOut" }}
      className="flex w-full max-w-lg flex-col items-center gap-8 px-4"
    >
      <PersonaAILogo />
      <ProgressDots currentStep={currentStep} />

      <Card className="w-full border-border/50 bg-surface shadow-xl">
        <CardContent className="flex flex-col gap-6 p-6 sm:p-8">
          <p className="text-balance text-center text-lg font-medium leading-relaxed text-foreground sm:text-xl">
            {question}
          </p>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              type="text"
              placeholder="Type your answer..."
              value={value}
              onChange={(e) => onChange(e.target.value)}
              className="h-11 text-base"
              autoFocus
              disabled={isSubmitting}
            />
            <Button type="submit" size="lg" className="h-11 w-full text-base" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : isLast ? "Complete" : "Next"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function PersonaTradingCard({ completeness, traits }: { completeness: number; traits: string[] }) {
  return (
    <motion.div
      key="trading-card"
      initial={{ opacity: 0, scale: 0.9, y: 30 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="flex w-full max-w-md flex-col items-center gap-6 px-4"
    >
      <PersonaAILogo />

      <div className="relative w-full rounded-2xl p-[2px]">
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary via-purple-400 to-primary/50" />
        <Card className="relative w-full border-0 bg-surface shadow-2xl">
          <CardContent className="flex flex-col items-center gap-6 p-6 sm:p-8">
            <h2 className="text-center text-2xl font-bold text-foreground sm:text-3xl">
              Your AI Twin is Ready
            </h2>

            <div className="flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2">
              <span className="text-sm font-medium text-foreground">
                Persona Created
              </span>
              <div className="flex h-5 w-5 items-center justify-center rounded-full bg-primary">
                <Check className="h-3 w-3 text-primary-foreground" strokeWidth={3} />
              </div>
            </div>

            <div className="flex flex-wrap justify-center gap-2">
              {traits.map((trait) => (
                <Badge key={trait} variant="default" className="px-3 py-1 text-sm">
                  {trait}
                </Badge>
              ))}
            </div>

            <CompletenessRing percentage={completeness} />

            <div className="flex w-full gap-3">
              <Link href="/chat" className="flex-1">
                <Button size="lg" variant="default" className="h-11 w-full text-base">
                  Chat with your Twin
                </Button>
              </Link>
              <Link href="/dashboard" className="flex-1">
                <Button size="lg" variant="outline" className="h-11 w-full text-base">
                  Dashboard
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </motion.div>
  );
}

function OnboardingNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-center px-4 py-3 sm:px-6">
        <Link
          href="/"
          className="absolute left-4 text-lg font-semibold tracking-tight text-primary sm:left-6 sm:text-xl"
        >
          PersonaAI
        </Link>
      </div>
      <nav className="mx-auto flex max-w-7xl items-center justify-center gap-1 border-t border-border px-4 py-2 sm:gap-6 sm:px-6">
        {NAV_LINKS.map((link) => {
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/15 text-primary"
                  : "text-muted-foreground hover:bg-white/5 hover:text-white"
              )}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}

export function OnboardingWizard() {
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<string[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [completeness, setCompleteness] = useState(0);
  const [questions, setQuestions] = useState<{ id: string; text: string }[]>([]);

  useEffect(() => {
    const storedUserId = localStorage.getItem("user_id");
    if (storedUserId) {
      setUserId(storedUserId);
    }

    const fetchQuestions = async () => {
      try {
        const token = localStorage.getItem("access_token") || "";
        const res = await fetch(`${API_URL}/questions/starter`, {
          headers: { "Authorization": `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          const qs = data.questions.map((q: string, i: number) => ({
            id: `starter-${i}`,
            text: q,
          }));
          setQuestions(qs);
          setAnswers(Array(qs.length).fill(""));
        }
      } catch (e) {
        console.error("Failed to fetch questions:", e);
        const fallback = [
          { id: "q1", text: "Hey! What's your name?" },
          { id: "q2", text: "What do you do — are you working, studying, or both?" },
          { id: "q3", text: "What are you passionate about or interested in?" },
          { id: "q4", text: "How would you describe your personality in a few words?" },
          { id: "q5", text: "What's one goal you're really working towards right now?" },
        ];
        setQuestions(fallback);
        setAnswers(Array(fallback.length).fill(""));
      }
    };
    fetchQuestions();
  }, []);

  const submitAnswer = async (questionText: string, answer: string) => {
    if (!userId) return;

    try {
      const token = localStorage.getItem("access_token") || "";
      const response = await fetch(`${API_URL}/questions/answer`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: userId,
          question: questionText,
          answer: answer,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.accepted) {
          // Update persona after each accepted answer
          const personaResponse = await fetch(`${API_URL}/persona/${userId}/completeness`, {
            headers: { "Authorization": `Bearer ${token}` },
          });
          if (personaResponse.ok) {
            const personaData = await personaResponse.json();
            setCompleteness(personaData.completeness * 100);
          }
        }
      }
    } catch (error) {
      console.error("Failed to submit answer:", error);
    }
  };

  const handleNext = async () => {
    setIsSubmitting(true);

    // Submit the current answer to the API
    const currentQuestion = questions[currentStep];
    if (answers[currentStep].trim()) {
      await submitAnswer(currentQuestion.text, answers[currentStep]);
    }

    if (currentStep < TOTAL_STEPS - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      setIsComplete(true);
    }

    setIsSubmitting(false);
  };

  const handleAnswerChange = (value: string) => {
    setAnswers((prev) => {
      const updated = [...prev];
      updated[currentStep] = value;
      return updated;
    });
  };

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <OnboardingNav />
      <div className="flex flex-1 items-center justify-center py-8">
        <AnimatePresence mode="wait">
          {isComplete ? (
            <PersonaTradingCard completeness={completeness} traits={answers.filter(Boolean)} />
          ) : (
            <QuestionStep
              key={currentStep}
              currentStep={currentStep}
              question={questions[currentStep]?.text || ""}
              value={answers[currentStep]}
              onChange={handleAnswerChange}
              onNext={handleNext}
              isLast={currentStep === TOTAL_STEPS - 1}
              isSubmitting={isSubmitting}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
