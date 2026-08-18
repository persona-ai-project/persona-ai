"use client";

import { use } from "react";
import { TwinDetail } from "@/components/dashboard/TwinDetail";

export default function TwinDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <TwinDetail twinId={id} />;
}
