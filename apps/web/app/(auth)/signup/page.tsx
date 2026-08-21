import Link from "next/link";
import { AuthCard } from "@/components/auth/AuthCard";
import { SignUpForm } from "@/components/auth/SignUpForm";

export const metadata = {
  title: "Sign Up | PersonaAI",
  description: "Create your PersonaAI account and build your digital twin",
};

export default function SignUpPage() {
  return (
    <AuthCard
      heading="Create your account"
      subheading="Sign up to get started"
      icon={
        <svg className="w-7 h-7 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zM4 19.235v-.11a6.375 6.375 0 0112.75 0v.109A12.318 12.318 0 0110.374 21c-2.331 0-4.512-.645-6.374-1.766z" />
        </svg>
      }
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-gold-500 hover:text-gold-400 transition-colors">
            Log in
          </Link>
        </>
      }
    >
      <SignUpForm />
    </AuthCard>
  );
}
