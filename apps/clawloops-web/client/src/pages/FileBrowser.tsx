import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { AppShell } from '@/components/layout/AppShell';
import { RequireAuth } from '@/components/guards/RouteGuard';
import { PageHeader, LoadingCard, ErrorDisplay } from '@/components/shared/PageComponents';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Folder,
  File,
  ChevronLeft,
  RefreshCw,
  Edit,
  Save,
  X,
  Trash2,
  Plus,
  ArrowUp,
  Upload,
  Download,
} from 'lucide-react';
import { toast } from 'sonner';

interface FileItem {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: string;
}

function FileBrowserContent() {
  const { user } = useAuth();
  const [files, setFiles] = useState<FileItem[]>([]);
  const [currentPath, setCurrentPath] = useState<string>('/home/node/.openclaw/workspace');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  const [showNewFileDialog, setShowNewFileDialog] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const loadFiles = useCallback(async (path: string) => {
    console.log('Loading files for path:', path);
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/files/list?path=${encodeURIComponent(path)}`, {
        credentials: 'include',
      });
      console.log('Files list response status:', res.status);
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        if (errorData.detail && errorData.detail.includes('No container available')) {
          throw new Error('工作区未启动，请先启动工作区再访问文件管理');
        }
        throw new Error('Failed to load files');
      }
      const data = await res.json();
      console.log('Files list response data:', data);
      setFiles(data.files || []);
      console.log('Updated files state:', data.files || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载文件失败');
      console.error('Error loading files:', e);
    } finally {
      setLoading(false);
      console.log('File loading completed');
    }
  }, []);

  useEffect(() => {
    loadFiles(currentPath);
  }, [currentPath, loadFiles]);

  const readFile = async (file: FileItem) => {
    try {
      const res = await fetch(`/api/v1/files/read?path=${encodeURIComponent(file.path)}`, {
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to read file');
      const data = await res.json();
      setFileContent(data.content || '');
      setSelectedFile(file);
      setIsEditing(true);
    } catch (e) {
      toast.error('读取文件失败');
    }
  };

  const saveFile = async () => {
    if (!selectedFile) return;
    setIsSaving(true);
    try {
      const res = await fetch('/api/v1/files/write', {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: selectedFile.path,
          content: fileContent,
        }),
      });
      if (!res.ok) throw new Error('Failed to save file');
      toast.success('文件保存成功');
      setIsEditing(false);
    } catch (e) {
      toast.error('保存文件失败');
    } finally {
      setIsSaving(false);
    }
  };

  const handleFileClick = (file: FileItem) => {
    if (file.type === 'directory') {
      setCurrentPath(file.path);
    } else {
      readFile(file);
    }
  };

  const goBack = () => {
    if (currentPath === '/') return;
    const parentPath = currentPath.split('/').slice(0, -1).join('/') || '/';
    setCurrentPath(parentPath);
  };

  const createNewFile = async () => {
    if (!newFileName.trim()) return;
    const newPath = `${currentPath}/${newFileName.trim()}`;
    try {
      const res = await fetch('/api/v1/files/write', {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: newPath,
          content: '',
        }),
      });
      if (!res.ok) throw new Error('Failed to create file');
      toast.success('文件创建成功');
      setShowNewFileDialog(false);
      setNewFileName('');
      loadFiles(currentPath);
    } catch (e) {
      toast.error('创建文件失败');
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadFiles = event.target.files;
    if (!uploadFiles || uploadFiles.length === 0) return;

    setIsUploading(true);
    try {
      let hasSuccess = false;
      let hasUploadAttempt = false;
      for (const file of uploadFiles) {
        hasUploadAttempt = true;
        // 检查当前目录中是否已存在同名文件
        const hasSameName = files.some(f => f.name === file.name);
        if (hasSameName) {
          toast.error('有重名文件,无法上传');
          continue;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('path', `${currentPath}/${file.name}`);

        const res = await fetch('/api/v1/files/upload', {
          method: 'POST',
          credentials: 'include',
          body: formData,
        });

        if (!res.ok) {
          const errorData = await res.json().catch(() => ({}));
          if (errorData.detail && (errorData.detail.includes('File already exists') || errorData.detail.includes('FILE_ALREADY_EXISTS'))) {
            toast.error('有重名文件,无法上传');
          } else {
            throw new Error('Failed to upload file');
          }
          continue;
        }
        hasSuccess = true;
      }
      if (hasUploadAttempt) {
        loadFiles(currentPath);
        if (hasSuccess) {
          toast.success('文件上传成功');
        }
      }
    } catch (e) {
      toast.error('文件上传失败');
    } finally {
      setIsUploading(false);
      // 重置文件输入框，允许重新选择相同的文件
      event.target.value = '';
    }
  };

  const handleFileDownload = async (file: FileItem) => {
    try {
      const res = await fetch(`/api/v1/files/download?path=${encodeURIComponent(file.path)}`, {
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to download file');

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('文件下载成功');
    } catch (e) {
      toast.error('文件下载失败');
    }
  };

  return (
    <div className="page-enter">
      <PageHeader
        title="文件管理"
        description="管理容器内的文件"
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowNewFileDialog(true)}
            >
              <Plus className="w-4 h-4 mr-1" />
              新建文件
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => document.getElementById('file-upload')?.click()}
              disabled={isUploading}
            >
              <Upload className="w-4 h-4 mr-1" />
              上传文件
            </Button>
            <input
              id="file-upload"
              type="file"
              multiple
              onChange={handleFileUpload}
              className="hidden"
            />
            <Button
              variant="ghost"
              size="icon"
              onClick={() => loadFiles(currentPath)}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <Card className="lg:col-span-2 card-glow">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={goBack}
                disabled={currentPath === '/'}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <div className="flex-1">
                <CardTitle className="text-base flex items-center gap-2">
                  <ArrowUp className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground mono">{currentPath}</span>
                </CardTitle>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading && (
              <LoadingCard />
            )}
            {error && (
              <ErrorDisplay message={error} onRetry={() => loadFiles(currentPath)} />
            )}
            {!loading && !error && (
              <div className="space-y-1">
                {files.map((file) => (
                  <button
                    key={file.path}
                    onClick={() => handleFileClick(file)}
                    className="w-full text-left px-3 py-2 rounded-md hover:bg-white/5 transition-colors flex items-center gap-2"
                  >
                    {file.type === 'directory' ? (
                      <Folder className="w-4 h-4 text-yellow-400 flex-shrink-0" />
                    ) : (
                      <File className="w-4 h-4 text-blue-400 flex-shrink-0" />
                    )}
                    <span className="text-sm flex-1 truncate">{file.name}</span>
                    {file.size && (
                      <span className="text-xs text-muted-foreground mono">
                        {file.size} bytes
                      </span>
                    )}
                    {file.type === 'file' && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleFileDownload(file);
                        }}
                      >
                        <Download className="w-3.5 h-3.5" />
                      </Button>
                    )}
                  </button>
                ))}
                {files.length === 0 && (
                  <div className="text-center py-6 text-sm text-muted-foreground">
                    该目录为空
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="card-glow">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">
                {selectedFile ? selectedFile.name : '文件编辑'}
              </CardTitle>
              {selectedFile && (
                <div className="flex items-center gap-1">
                  {isEditing ? (
                    <>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => setIsEditing(false)}
                        disabled={isSaving}
                      >
                        <X className="w-3.5 h-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={saveFile}
                        disabled={isSaving}
                      >
                        <Save className="w-3.5 h-3.5" />
                      </Button>
                    </>
                  ) : (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => setIsEditing(true)}
                    >
                      <Edit className="w-3.5 h-3.5" />
                    </Button>
                  )}
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {selectedFile ? (
              isEditing ? (
                <Textarea
                  value={fileContent}
                  onChange={(e) => setFileContent(e.target.value)}
                  className="h-[500px] font-mono text-xs"
                  placeholder="文件内容..."
                />
              ) : (
                <div className="h-[500px] overflow-auto">
                  <pre className="text-xs font-mono whitespace-pre-wrap text-muted-foreground">
                    {fileContent || '(文件为空)'}
                  </pre>
                </div>
              )
            ) : (
              <div className="h-[500px] flex items-center justify-center text-sm text-muted-foreground">
                选择一个文件进行查看或编辑
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={showNewFileDialog} onOpenChange={setShowNewFileDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建文件</DialogTitle>
            <DialogDescription>
              输入新文件的名称
            </DialogDescription>
          </DialogHeader>
          <Input
            value={newFileName}
            onChange={(e) => setNewFileName(e.target.value)}
            placeholder="文件名"
            autoFocus
          />
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowNewFileDialog(false)}
            >
              取消
            </Button>
            <Button onClick={createNewFile}>
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function FileBrowserPage() {
  return (
    <RequireAuth>
      <AppShell>
        <FileBrowserContent />
      </AppShell>
    </RequireAuth>
  );
}
