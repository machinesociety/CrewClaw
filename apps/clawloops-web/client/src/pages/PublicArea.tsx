import { useCallback, useEffect, useMemo, useState } from 'react';
import { Redirect, useLocation, useSearch } from 'wouter';
import { useAuth } from '@/contexts/AuthContext';
import { AppShell } from '@/components/layout/AppShell';
import { RequireAuth } from '@/components/guards/RouteGuard';
import { PageHeader, LoadingCard, ErrorDisplay } from '@/components/shared/PageComponents';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  Folder,
  File,
  FileText,
  FileImage,
  FileArchive,
  FileSpreadsheet,
  FileAudio,
  FileVideo,
  FileJson,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Upload,
  Download,
  Trash2,
  Plus,
} from 'lucide-react';
import { toast } from 'sonner';

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
  let value = bytes;
  while (value >= 1024 && idx < units.length - 1) {
    value /= 1024;
    idx += 1;
  }
  return `${value.toFixed(idx === 0 ? 0 : 1)} ${units[idx]}`;
}

function joinPath(dir: string, name: string) {
  return dir ? `${dir}/${name}` : name;
}

function parentPath(dir: string) {
  if (!dir) return '';
  const parts = dir.split('/').filter(Boolean);
  parts.pop();
  return parts.join('/');
}

function useQueryState(basePath: string): [
  { path: string; page: number },
  (nextPath: string) => void,
  (nextPage: number) => void,
] {
  const [, setLocation] = useLocation();
  const search = useSearch();
  const state = useMemo(() => {
    const params = new URLSearchParams(search);
    const path = params.get('path') || '';
    const pageRaw = params.get('page') || '1';
    const pageNum = Number.parseInt(pageRaw, 10);
    const page = Number.isFinite(pageNum) && pageNum > 0 ? pageNum : 1;
    return { path, page };
  }, [search]);

  const setPath = useCallback(
    (next: string) => {
      const clean = next.replace(/^\/+/, '').replace(/\/+$/, '');
      if (!clean) {
        setLocation(`${basePath}?page=1`);
        return;
      }
      setLocation(`${basePath}?path=${encodeURIComponent(clean)}&page=1`);
    },
    [basePath, setLocation]
  );

  const setPage = useCallback(
    (nextPage: number) => {
      const p = Number.isFinite(nextPage) && nextPage > 0 ? nextPage : 1;
      const cleanPath = state.path.replace(/^\/+/, '').replace(/\/+$/, '');
      if (!cleanPath) {
        setLocation(`${basePath}?page=${p}`);
        return;
      }
      setLocation(`${basePath}?path=${encodeURIComponent(cleanPath)}&page=${p}`);
    },
    [basePath, setLocation, state.path]
  );

  return [state, setPath, setPage];
}

export function PublicAreaView({ mode, basePath }: { mode: 'user' | 'admin'; basePath: string }) {
  const { user, isAdmin } = useAuth();
  const [qs, setCurrentPath, setPage] = useQueryState(basePath);
  const currentPath = qs.path;
  const page = qs.page;
  const scope = mode === 'admin' ? 'global' : 'user';
  const [entries, setEntries] = useState<PublicEntry[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [rootPath, setRootPath] = useState('/var/lib/clawloops/shared/public/files');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [showNewFolderDialog, setShowNewFolderDialog] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');

  const allowDelete = mode === 'admin' ? isAdmin : true;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `/api/v1/public-area/files/list?path=${encodeURIComponent(currentPath)}&page=${page}&scope=${scope}`,
        { credentials: 'include' }
      );
      if (!res.ok) throw new Error('加载失败');
      const data = await res.json();
      setEntries(data.entries || []);
      setRootPath(data.rootPath || '/var/lib/clawloops/shared/public/files');
      const tp = data.totalPages || 1;
      setTotalPages(tp);
      if (page > tp) {
        setPage(tp);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败');
    } finally {
      setLoading(false);
    }
  }, [currentPath, page, scope, setPage]);

  useEffect(() => {
    load();
  }, [load]);

  const openDir = (name: string) => setCurrentPath(joinPath(currentPath, name));
  const goUp = () => {
    if (!currentPath) {
      toast.error('不允许再回退');
      return;
    }
    setCurrentPath(parentPath(currentPath));
  };

  const createFolder = async () => {
    const folder = newFolderName.trim().replace(/\/+$/, '');
    if (!folder) return;
    try {
      const form = new FormData();
      form.append('path', joinPath(currentPath, folder));
      form.append('scope', scope);
      const res = await fetch('/api/v1/public-area/files/mkdir', {
        method: 'POST',
        credentials: 'include',
        body: form,
      });
      if (!res.ok) throw new Error('创建失败');
      toast.success('已创建');
      setShowNewFolderDialog(false);
      setNewFolderName('');
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '创建失败');
    }
  };

  const uploadFiles = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    setIsUploading(true);
    try {
      for (const file of files) {
        const form = new FormData();
        form.append('path', joinPath(currentPath, file.name));
        form.append('file', file);
        form.append('scope', scope);
        if (mode === 'admin' && isAdmin) form.append('overwrite', 'true');
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
      setIsUploading(false);
      event.target.value = '';
    }
  };

  const downloadFile = async (name: string) => {
    const path = joinPath(currentPath, name);
    try {
      const res = await fetch(
        `/api/v1/public-area/files/download?path=${encodeURIComponent(path)}&scope=${scope}`,
        { credentials: 'include' }
      );
      if (!res.ok) throw new Error('下载失败');
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '下载失败');
    }
  };

  const deletePath = async (name: string) => {
    const path = joinPath(currentPath, name);
    try {
      const res = await fetch(
        `/api/v1/public-area/files/delete?path=${encodeURIComponent(path)}&scope=${scope}`,
        { method: 'DELETE', credentials: 'include' }
      );
      if (!res.ok) throw new Error('删除失败');
      toast.success('已删除');
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '删除失败');
    }
  };

  const title = mode === 'admin' ? '公共区域管理' : '公共区域';
  const desc =
    mode === 'admin'
      ? '以目录路径管理公共文件（支持覆盖与删除）'
      : '以目录路径浏览并上传/下载公共文件（仅容器副本）';

  const iconForFile = (name: string) => {
    const ext = name.toLowerCase().split('.').pop() || '';
    if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) return FileImage;
    if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'].includes(ext)) return FileArchive;
    if (['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'].includes(ext)) return FileAudio;
    if (['mp4', 'mov', 'mkv', 'webm', 'avi'].includes(ext)) return FileVideo;
    if (['csv', 'xls', 'xlsx'].includes(ext)) return FileSpreadsheet;
    if (['json'].includes(ext)) return FileJson;
    if (['md', 'txt', 'log', 'yaml', 'yml', 'toml', 'ini', 'env'].includes(ext)) return FileText;
    return File;
  };

  return (
    <div className="page-enter">
      <PageHeader
        title={title}
        description={desc}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowNewFolderDialog(true)}
              disabled={isUploading}
            >
              <Plus className="w-4 h-4 mr-1" />
              新建文件夹
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => document.getElementById(`public-upload-${mode}`)?.click()}
              disabled={isUploading}
            >
              <Upload className="w-4 h-4 mr-1" />
              上传
            </Button>
            <input id={`public-upload-${mode}`} type="file" multiple onChange={uploadFiles} className="hidden" />
            <Button variant="ghost" size="icon" onClick={load} disabled={loading}>
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        }
      />

      {loading && <LoadingCard />}
      {error && <ErrorDisplay message={error} />}

      {!loading && !error && (
        <div className="grid grid-cols-1 gap-5">
          <Card className="card-glow">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={goUp}
                  disabled={!currentPath}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <CardTitle className="text-base flex items-center gap-2">
                  <span className="text-muted-foreground">/</span>
                  <span className="truncate">{currentPath ? `${rootPath}/${currentPath}` : rootPath}</span>
                </CardTitle>
                <div className="ml-auto text-xs text-muted-foreground mono">
                  {user?.userId}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {entries.length === 0 ? (
                <div className="text-sm text-muted-foreground">目录为空</div>
              ) : (
                entries.map((e) => (
                  <div
                    key={e.name}
                    className="flex items-center justify-between rounded-md border border-border/50 px-3 py-2"
                  >
                    <button
                      className="flex items-center gap-2 min-w-0 flex-1 text-left"
                      onClick={() => (e.isDir ? openDir(e.name) : undefined)}
                    >
                      {e.isDir ? (
                        <Folder className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      ) : (
                        (() => {
                          const Icon = iconForFile(e.name);
                          return <Icon className="w-4 h-4 text-muted-foreground flex-shrink-0" />;
                        })()
                      )}
                      <div className="min-w-0">
                        <div className="text-sm font-medium truncate">{e.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {e.isDir ? '目录' : formatBytes(e.size)}
                        </div>
                      </div>
                    </button>
                    <div className="flex items-center gap-2">
                      {!e.isDir && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => downloadFile(e.name)}
                        >
                          <Download className="w-4 h-4 mr-1" />
                          下载
                        </Button>
                      )}
                      {allowDelete && (
                        <Button
                          variant="destructive"
                          size="icon"
                          onClick={() => deletePath(e.name)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              )}

              {totalPages > 1 && (
                <div className="flex items-center justify-end gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page - 1)}
                    disabled={page <= 1}
                  >
                    上一页
                  </Button>
                  <div className="text-xs text-muted-foreground mono">
                    {page} / {totalPages}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page + 1)}
                    disabled={page >= totalPages}
                  >
                    下一页
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

        </div>
      )}

      <Dialog open={showNewFolderDialog} onOpenChange={setShowNewFolderDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建文件夹</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground mono truncate">/{currentPath || ''}</div>
            <Input value={newFolderName} onChange={(e) => setNewFolderName(e.target.value)} placeholder="folder-name" />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewFolderDialog(false)}>
              取消
            </Button>
            <Button onClick={createFolder} disabled={!newFolderName.trim()}>
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function PublicAreaPage() {
  const { isAdmin } = useAuth();
  if (isAdmin) {
    return <Redirect to="/admin/public-area" />;
  }
  return (
    <RequireAuth>
      <AppShell>
        <PublicAreaView mode="user" basePath="/public-area" />
      </AppShell>
    </RequireAuth>
  );
}
