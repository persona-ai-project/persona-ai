"use client";

import { use } from "react";
import { PublicProfile } from "@/components/directory/PublicProfile";

export default function PublicProfilePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  return <PublicProfile slug={slug} />;
}
