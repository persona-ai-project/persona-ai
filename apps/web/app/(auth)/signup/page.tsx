import Link from "next/link";

import { AuthCard } from "@/components/auth/AuthCard";
import { SignUpForm } from "@/components/auth/SignUpForm";

export const metadata = {
  title: "Sign Up | PersonaAI",
  description: "Create your free PersonaAI account and build your AI digital twin",
};

export default function SignUpPage() {
  return (
    <AuthCard
      heading="Create your AI Twin"
      subheading="Start with your free account"
      footer={
        <>
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-medium text-primary transition-colors hover:text-primary/80"
          >
            Log in
          </Link>
        </>
      }
    >
      <SignUpForm />
    </AuthCard>
  );
}
