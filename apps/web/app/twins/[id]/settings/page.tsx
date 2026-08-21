"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { NavBar } from "@/components/layout/NavBar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { API_URL } from "@/lib/config";

export default function TwinSettingsPage({ params }: { params: { id: string } }) {
  const id = params.id;
  const router = useRouter();
  const [twin, setTwin] = useState<any>(null);
  const [name, setName] = useState("");
  const [tagline, setTagline] = useState("");
  const [bio, setBio] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    fetch(`${API_URL}/twins/${id}`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((data) => {
        setTwin(data);
        setName(data.name || "");
        setTagline(data.tagline || "");
        setBio(data.bio || "");
      });
  }, [id]);

  const handleSave = async () => {
    setSaving(true);
    setMsg("");
    const token = localStorage.getItem("access_token");
    try {
      const r = await fetch(`${API_URL}/twins/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ name, tagline, bio }),
      });
      if (r.ok) {
        setMsg("Saved successfully");
      } else {
        setMsg("Failed to save");
      }
    } catch {
      setMsg("Network error");
    }
    setSaving(false);
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this twin? This cannot be undone.")) return;
    const token = localStorage.getItem("access_token");
    const r = await fetch(`${API_URL}/twins/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (r.ok) router.push("/dashboard");
  };

  return (
    <AuthGuard>
      <NavBar />
      <div className="container mx-auto py-8 max-w-2xl">
        <h1 className="text-2xl font-bold text-white mb-6">Twin Settings</h1>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm text-muted-foreground">Name</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} className="mt-1" />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Tagline</label>
              <Input value={tagline} onChange={(e) => setTagline(e.target.value)} className="mt-1" placeholder="One-line description" />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Bio</label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                rows={4}
                placeholder="Tell people about this twin..."
              />
            </div>
            {msg && <p className="text-sm text-green-400">{msg}</p>}
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "Saving..." : "Save Changes"}
            </Button>
          </CardContent>
        </Card>

        <Card className="border-red-800">
          <CardHeader>
            <CardTitle className="text-red-400">Danger Zone</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Permanently delete this twin and all its data. This action cannot be undone.
            </p>
            <Button variant="destructive" onClick={handleDelete}>Delete Twin</Button>
          </CardContent>
        </Card>
      </div>
    </AuthGuard>
  );
}
