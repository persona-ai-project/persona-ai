"use client";

import { useState, useEffect, useRef } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { NavBar } from "@/components/layout/NavBar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { API_URL } from "@/lib/config";

export default function TwinSourcesPage({ params }: { params: { id: string } }) {
  const id = params.id;
  const [sources, setSources] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [url, setUrl] = useState("");
  const [msg, setMsg] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const headers = { Authorization: `Bearer ${token}` };

  const loadSources = () => {
    if (!token) return;
    fetch(`${API_URL}/twins/${id}/sources`, { headers })
      .then((r) => r.json())
      .then((data) => setSources(Array.isArray(data) ? data : data.sources || []));
  };

  useEffect(() => { loadSources(); }, [id]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setMsg("");
    const form = new FormData();
    form.append("file", file);
    try {
      const r = await fetch(`${API_URL}/twins/${id}/sources/file`, {
        method: "POST", headers, body: form,
      });
      if (r.ok) { setMsg("File uploaded and processing"); loadSources(); }
      else { setMsg("Upload failed"); }
    } catch { setMsg("Network error"); }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = "";
  };

  const handleUrlSubmit = async () => {
    if (!url.trim()) return;
    setUploading(true);
    setMsg("");
    try {
      const r = await fetch(`${API_URL}/twins/${id}/sources/url`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });
      if (r.ok) { setMsg("URL submitted for processing"); setUrl(""); loadSources(); }
      else { setMsg("Failed to submit URL"); }
    } catch { setMsg("Network error"); }
    setUploading(false);
  };

  const handleDelete = async (sourceId: string) => {
    if (!confirm("Delete this source?")) return;
    await fetch(`${API_URL}/twins/${id}/sources/${sourceId}`, { method: "DELETE", headers });
    loadSources();
  };

  return (
    <AuthGuard>
      <NavBar />
      <div className="container mx-auto py-8 max-w-3xl">
        <h1 className="text-2xl font-bold text-white mb-6">Manage Sources</h1>

        <Card className="mb-6">
          <CardHeader><CardTitle>Upload File</CardTitle></CardHeader>
          <CardContent>
            <input ref={fileRef} type="file" accept=".pdf,.docx,.doc,.md,.txt" onChange={handleFileUpload} className="hidden" />
            <Button onClick={() => fileRef.current?.click()} disabled={uploading}>
              {uploading ? "Uploading..." : "Choose File"}
            </Button>
            <p className="text-xs text-muted-foreground mt-2">PDF, DOCX, MD, TXT</p>
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader><CardTitle>Add URL</CardTitle></CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com/article" className="flex-1" />
              <Button onClick={handleUrlSubmit} disabled={uploading || !url.trim()}>Add</Button>
            </div>
          </CardContent>
        </Card>

        {msg && <p className="text-sm text-green-400 mb-4">{msg}</p>}

        <Card>
          <CardHeader><CardTitle>Sources ({sources.length})</CardTitle></CardHeader>
          <CardContent>
            {sources.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">No sources yet</p>
            ) : (
              <div className="space-y-3">
                {sources.map((s) => (
                  <div key={s.id} className="flex items-center justify-between rounded-lg border p-3">
                    <div>
                      <p className="font-medium text-white">{s.title || s.source_type}</p>
                      <p className="text-xs text-muted-foreground">{s.status || "indexed"}</p>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(s.id)}>Delete</Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AuthGuard>
  );
}
