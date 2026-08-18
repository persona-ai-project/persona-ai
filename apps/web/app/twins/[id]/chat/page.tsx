"use client";

import { use } from "react";
import { TwinChat } from "@/components/chat/TwinChat";

export default function TwinChatPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <TwinChat twinId={id} />;
}
