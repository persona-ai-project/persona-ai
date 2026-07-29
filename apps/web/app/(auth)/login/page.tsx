import Link from "next/link";

import { AuthCard } from "@/components/auth/AuthCard";
import { LoginForm } from "@/components/auth/LoginForm";

export const metadata = {
  title: "Log In | PersonaAI",
  description: "Sign in to your PersonaAI account and access your AI digital twin",
};

export default function LoginPage() {
  return (
    <AuthCard
      heading="Welcome back"
      subheading="Sign in to your AI Twin"
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link
            href="/signup"
            className="font-medium text-primary transition-colors hover:text-primary/80"
          >
            Sign up
          </Link>
        </>
      }
    >
      <LoginForm />
    </AuthCard>
  );
}
