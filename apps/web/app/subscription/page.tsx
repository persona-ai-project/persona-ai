import { SubscriptionManager } from "@/components/subscription/SubscriptionManager";

export const metadata = {
  title: "Subscription | PersonaAI",
  description: "Manage your subscription and billing",
};

export default function SubscriptionPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <h1 className="mb-8 text-2xl font-bold text-white">Subscription</h1>
      <SubscriptionManager />
    </div>
  );
}
