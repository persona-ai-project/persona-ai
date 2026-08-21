"use client";

import { TwinDetail } from "@/components/dashboard/TwinDetail";

export default function TwinDetailPage({ params }: { params: { id: string } }) {
  return <TwinDetail twinId={params.id} />;
}
