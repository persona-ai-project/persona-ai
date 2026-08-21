"use client";

import { TwinChat } from "@/components/chat/TwinChat";

export default function TwinChatPage({ params }: { params: { id: string } }) {
  return <TwinChat twinId={params.id} />;
}
