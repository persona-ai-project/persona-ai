import { AnalyticsDashboard } from "@/components/analytics/AnalyticsDashboard";

export const metadata = {
  title: "Analytics | PersonaAI",
  description: "Platform insights and metrics",
};

export default function AnalyticsPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <AnalyticsDashboard />
    </div>
  );
}
