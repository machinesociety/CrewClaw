import { useCallback, useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { RequireAuth } from '@/components/guards/RouteGuard';
import { PageHeader, LoadingCard, ErrorDisplay } from '@/components/shared/PageComponents';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, Download, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

interface SkillFile {
  name: string;
  size: number;
  modifiedAt: number;
}

interface PublicEntry {
  name: string;
  isDir: boolean;
  size: number;
  modifiedAt: number;
}

function formatBytes(bytes: number) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let idx = 0;
  let v = bytes;
  while (v >= 1024 && idx < units.length - 1) {
    v /= 1024;
    idx += 1;
  }
  return `${v.toFixed(idx === 0 ? 0 : 1)} ${units[idx]}`;
}

function SkillsContent() {
  const [publicSkills, setPublicSkills] = useState<SkillFile[]>([]);
  const [publicFiles, setPublicFiles] = useState<PublicEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [skillsRes, filesRes] = await Promise.all([
        fetch('/api/v1/public-area/skills/list', { credentials: 'include' }),
        fetch('/api/v1/public-area/files/list', { credentials: 'include' }),
      ]);
      if (!skillsRes.ok) throw new Error('加载公共 Skills 失败');
      if (!filesRes.ok) throw new Error('加载公共文件失败');
      const skillsData = await skillsRes.json();
      const filesData = await filesRes.json();
      setPublicSkills(skillsData.files || []);
      setPublicFiles((filesData.entries || []).filter((e: PublicEntry) => !e.isDir));
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const uploadPublicSkill = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      for (const f of files) {
        const form = new FormData();
        form.append('file', f);
        const res = await fetch('/api/v1/public-area/skills/upload', {
          method: 'POST',
          credentials: 'include',
          body: form,
        });
        if (!res.ok) throw new Error('上传失败');
      }
      toast.success('上传成功');
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '上传失败');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const uploadPublicFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      for (const f of files) {
        const form = new FormData();
        form.append('path', f.name);
        form.append('file', f);
        const res = await fetch('/api/v1/public-area/files/upload', {
          method: 'POST',
          credentials: 'include',
          body: form,
        });
        if (!res.ok) throw new Error('上传失败');
      }
      toast.success('上传成功');
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '上传失败');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const downloadSkill = async (name: string) => {
    try {
      const res = await fetch(`/api/v1/public-area/skills/download?name=${encodeURIComponent(name)}`, {
        credentials: 'include',
      });
      if (!res.ok) throw new Error('下载失败');
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `${name}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '下载失败');
    }
  };

  const downloadFile = async (path: string) => {
    try {
      const res = await fetch(`/api/v1/public-area/files/download?path=${encodeURIComponent(path)}`, {
        credentials: 'include',
      });
      if (!res.ok) throw new Error('下载失败');
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = path.split('/').pop() || 'download';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '下载失败');
    }
  };

  return (
    <div className="page-enter">
      <PageHeader
        title="公共区域"
        description="上传/下载公共文件与 Skills；运行时会只读挂载 Skills 供 OpenClaw 使用"
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => document.getElementById('public-file-upload')?.click()}
              disabled={uploading}
            >
              <Upload className="w-4 h-4 mr-1" />
              上传文件
            </Button>
            <input
              id="public-file-upload"
              type="file"
              multiple
              onChange={uploadPublicFile}
              className="hidden"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => document.getElementById('public-skill-upload')?.click()}
              disabled={uploading}
            >
              <Upload className="w-4 h-4 mr-1" />
              上传 Skill
            </Button>
            <input
              id="public-skill-upload"
              type="file"
              multiple
              onChange={uploadPublicSkill}
              className="hidden"
            />
            <Button variant="ghost" size="icon" onClick={load} disabled={loading}>
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        }
      />

      {loading && <LoadingCard />}
      {error && <ErrorDisplay title="加载失败" message={error} />}

      {!loading && !error && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <Card className="card-glow">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">公共文件</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {publicFiles.length === 0 ? (
                <div className="text-sm text-muted-foreground">暂无文件</div>
              ) : (
                publicFiles.map((f) => (
                  <div
                    key={f.name}
                    className="flex items-center justify-between rounded-md border border-border/50 px-3 py-2"
                  >
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">{f.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {formatBytes(f.size)}
                      </div>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => downloadFile(f.name)}>
                      <Download className="w-4 h-4 mr-1" />
                      下载
                    </Button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card className="card-glow">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">公共 Skills</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {publicSkills.length === 0 ? (
                <div className="text-sm text-muted-foreground">暂无文件</div>
              ) : (
                publicSkills.map((f) => (
                  <div
                    key={f.name}
                    className="flex items-center justify-between rounded-md border border-border/50 px-3 py-2"
                  >
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">{f.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {formatBytes(f.size)}
                      </div>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => downloadSkill(f.name)}>
                      <Download className="w-4 h-4 mr-1" />
                      下载
                    </Button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default function SkillsPage() {
  return (
    <RequireAuth>
      <AppShell>
        <SkillsContent />
      </AppShell>
    </RequireAuth>
  );
}
