"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { API_URL } from "@/lib/config";

interface PublicTwin {
  id: string;
  name: string;
  slug: string;
  tagline: string | null;
  bio: string | null;
  avatar_url: string | null;
  verification_level: string;
  total_chats: number;
  avg_fidelity: number | null;
  created_at: string;
  category_name: string | null;
}

interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
}

export function TwinDirectory() {
  const [twins, setTwins] = useState<PublicTwin[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("");
  const [sort, setSort] = useState("popular");

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchTwins();
  }, [category, sort]);

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API_URL}/twins/categories/list`);
      if (res.ok) {
        const data = await res.json();
        setCategories(data.categories || []);
      }
    } catch (error) {
      console.error("Failed to fetch categories:", error);
    }
  };

  const fetchTwins = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (category) params.append("category", category);
      if (search) params.append("search", search);
      params.append("sort", sort);

      const res = await fetch(`${API_URL}/twins/public?${params}`);
      if (res.ok) {
        const data = await res.json();
        setTwins(data.twins || []);
      }
    } catch (error) {
      console.error("Failed to fetch twins:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchTwins();
  };

  const getVerificationBadge = (level: string) => {
    switch (level) {
      case "official":
        return <Badge className="bg-blue-500/20 text-blue-400">✓ Official</Badge>;
      case "id_verified":
        return <Badge className="bg-green-500/20 text-green-400">✓ Verified</Badge>;
      case "email_verified":
        return <Badge className="bg-yellow-500/20 text-yellow-400">✓ Email</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-dvh bg-background">
      {/* Hero */}
      <section className="border-b bg-gradient-to-b from-primary/10 to-background py-12">
        <div className="mx-auto max-w-7xl px-4 text-center sm:px-6">
          <h1 className="mb-4 text-4xl font-bold text-white">
            Twin Directory
          </h1>
          <p className="mb-8 text-lg text-muted-foreground">
            Discover and chat with AI digital twins
          </p>

          {/* Search */}
          <div className="mx-auto flex max-w-xl gap-2">
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search twins..."
              className="flex-1"
            />
            <Button onClick={handleSearch}>Search</Button>
          </div>
        </div>
      </section>

      {/* Filters */}
      <section className="border-b bg-surface/50 py-4">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-4 sm:px-6">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Category:</span>
            <Select value={category} onValueChange={(v) => { setCategory(v); }}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Categories</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={cat.slug}>
                    {cat.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Sort:</span>
            <Select value={sort} onValueChange={setSort}>
              <SelectTrigger className="w-[150px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="popular">Most Popular</SelectItem>
                <SelectItem value="newest">Newest</SelectItem>
                <SelectItem value="rating">Highest Rated</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </section>

      {/* Twins Grid */}
      <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        {loading ? (
          <div className="flex min-h-[400px] items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : twins.length === 0 ? (
          <div className="flex min-h-[400px] flex-col items-center justify-center text-center">
            <div className="mb-4 text-4xl">🔍</div>
            <h3 className="mb-2 text-lg font-medium text-white">
              No twins found
            </h3>
            <p className="text-muted-foreground">
              Try adjusting your search or filters
            </p>
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {twins.map((twin, index) => (
              <motion.div
                key={twin.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.3 }}
              >
                <Link href={`/t/${twin.slug}`}>
                  <Card className="h-full transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10">
                    <CardContent className="p-6">
                      <div className="mb-4 flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <Avatar className="h-12 w-12">
                            <AvatarFallback className="bg-primary/20 text-primary">
                              {twin.name.slice(0, 2).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <h3 className="font-semibold text-white">
                              {twin.name}
                            </h3>
                            {twin.category_name && (
                              <p className="text-xs text-muted-foreground">
                                {twin.category_name}
                              </p>
                            )}
                          </div>
                        </div>
                        {getVerificationBadge(twin.verification_level)}
                      </div>

                      {twin.tagline && (
                        <p className="mb-3 text-sm text-muted-foreground line-clamp-2">
                          {twin.tagline}
                        </p>
                      )}

                      {twin.bio && (
                        <p className="mb-4 text-xs text-muted-foreground line-clamp-3">
                          {twin.bio}
                        </p>
                      )}

                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{twin.total_chats.toLocaleString()} chats</span>
                        {twin.avg_fidelity && (
                          <span>{(twin.avg_fidelity * 100).toFixed(0)}% fidelity</span>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
