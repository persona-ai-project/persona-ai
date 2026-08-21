"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [userEmail, setUserEmail] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    // Decode JWT to get email
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      // Check if token is expired
      if (payload.exp && payload.exp * 1000 < Date.now()) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user_id");
        router.push("/login");
        return;
      }
      setUserEmail(payload.email || "");
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_id");
      router.push("/login");
      return;
    }

    setLoading(false);
  }, [router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar userEmail={userEmail} />
      <main className="flex-1 lg:ml-64 min-h-screen">
        {children}
      </main>
    </div>
  );
}
