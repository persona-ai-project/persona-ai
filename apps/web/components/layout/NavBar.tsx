"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/owner", label: "My Twins" },
  { href: "/directory", label: "Directory" },
  { href: "/chat", label: "Chat" },
  { href: "/analytics", label: "Analytics" },
  { href: "/onboarding", label: "Interview" },
] as const;

interface NavBarProps {
  title?: string;
  initials?: string;
  displayName?: string;
}

export function NavBar({ title = "Dashboard", initials, displayName }: NavBarProps) {
  const pathname = usePathname();

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");
    window.location.href = "/login";
  };

  return (
    <>
      <header className="sticky top-0 z-10 border-b border-white/8 bg-[#09090b]/95 backdrop-blur-sm">
        <div className="relative mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <Link
            href="/dashboard"
            className="text-lg font-semibold tracking-tight text-[#f59e0b] sm:text-xl"
          >
            PersonaAI
          </Link>

          <h1 className="absolute left-1/2 hidden -translate-x-1/2 text-sm font-medium text-[#fafafa] sm:block sm:text-base">
            {title}
          </h1>

          <div className="flex items-center gap-2 sm:gap-3">
            {displayName && (
              <span className="hidden text-sm font-medium text-[#fafafa] sm:inline">
                {displayName}
              </span>
            )}
            {initials && (
              <Avatar size="sm">
                <AvatarFallback className="bg-[#f59e0b] text-xs font-semibold text-[#09090b]">
                  {initials}
                </AvatarFallback>
              </Avatar>
            )}
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-[#a1a1aa] hover:text-[#fafafa]"
              onClick={handleLogout}
            >
              Logout
            </Button>
          </div>
        </div>

        <nav className="mx-auto flex max-w-7xl items-center justify-center gap-1 overflow-x-auto border-t border-white/8 px-4 py-2 sm:gap-6 sm:px-6">
          {NAV_LINKS.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-[#f59e0b]/10 text-[#f59e0b]"
                    : "text-[#a1a1aa] hover:bg-white/5 hover:text-[#fafafa]"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </header>
    </>
  );
}
