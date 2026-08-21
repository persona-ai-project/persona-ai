"use client";

import { PublicProfile } from "@/components/directory/PublicProfile";

export default function PublicProfilePage({ params }: { params: { slug: string } }) {
  return <PublicProfile slug={params.slug} />;
}
