import { Suspense } from "react";
import InterviewOnboarding from "@/components/onboarding/InterviewOnboarding";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Build Your Twin | PersonaAI",
  description: "Have a conversation with AI to build your digital twin",
};

export default function OnboardingPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-[#09090b]"><div className="w-8 h-8 border-2 border-[#f59e0b] border-t-transparent rounded-full animate-spin" /></div>}>
      <InterviewOnboarding />
    </Suspense>
  );
}
