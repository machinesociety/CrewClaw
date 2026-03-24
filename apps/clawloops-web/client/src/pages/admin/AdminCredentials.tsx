/**
 * Admin Provider Credentials Page - /admin/provider-credentials
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Per 页面调用流程_BFF编排.md §6.5
 * List, create, verify, delete provider credentials
 */

import { useCallback, useEffect, useState } from 'react';
import {
  adminApi,
  ProviderCredential,
  CreateCredentialRequest,
  isAppError,
} from '@/lib/api';
import { RequireAdmin } from '@/components/guards/RouteGuard';
import { AppShell } from '@/components/layout/AppShell';
import { StatusBadge } from '@/components/shared/StatusBadge';
import {
  PageHeader,
  LoadingRows,
  ErrorDisplay,
  EmptyState,
  MonoText,
  ConfirmDialog,
} from '@/components/shared/PageComponents';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import {
  RefreshCw,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Key,
  ShieldCheck,
} from 'lucide-react';

// ============================================================
// Create Credential Dialog
// ============================================================

interface CreateDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onCreated: () => void;
}

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'azure_openai', label: 'Azure OpenAI' },
  { value: 'google', label: 'Google Gemini' },
  { value: 'mistral', label: 'Mistral AI' },
  { value: 'custom', label: 'Custom / Other' },
];

function CreateCredentialDialog({ open, onOpenChange, onCreated }: CreateDialogProps) {
  const [form, setForm] = useState<CreateCredentialRequest>({
    provider: 'openai',
    name: '',
    apiKey: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.apiKey) {
      setError('API Key 为必填项');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await adminApi.credentials.create(form);
      toast.success('凭据已创建');
      onCreated();
      onOpenChange(false);
      setForm({ provider: 'openai', name: '', apiKey: '' });
    } catch (e) {
      setError(isAppError(e) ? e.message : '创建失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>添加 Provider 凭据</DialogTitle>
          <DialogDescription>
            添加 AI Provider 的 API 凭据，用于模型调用
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Provider</Label>
            <Select
              value={form.provider}
              onValueChange={(v) => setForm((f) => ({ ...f, provider: v }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PROVIDERS.map((p) => (
                  <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="credName">名称（可选）</Label>
            <Input
              id="credName"
              placeholder="例如：production-key"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="apiKey">API Key *</Label>
            <Input
              id="apiKey"
              type="password"
              placeholder="sk-..."
              value={form.apiKey}
              onChange={(e) => setForm((f) => ({ ...f, apiKey: e.target.value }))}
              required
              className="mono"
            />
          </div>

          {error && (
            <p className="text-xs text-destructive">{error}</p>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
              取消
            </Button>
            <Button type="submit" disabled={loading} className="gap-2">
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              添加凭据
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================
// Status variant helper
// ============================================================

function credStatusVariant(status?: string) {
  switch (status) {
    case 'valid': return 'success' as const;
    case 'invalid': return 'error' as const;
    case 'unverified': return 'neutral' as const;
    default: return 'neutral' as const;
  }
}

// ============================================================
// Main Page
// ============================================================

function AdminCredentialsContent() {
  const [credentials, setCredentials] = useState<ProviderCredential[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<ProviderCredential | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadCredentials = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminApi.credentials.list();
      setCredentials(res.credentials || []);
    } catch (e) {
      setError(isAppError(e) ? e.message : '加载凭据列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCredentials();
  }, [loadCredentials]);

  const handleVerify = async (cred: ProviderCredential) => {
    setActionLoading(cred.credentialId + '_verify');
    try {
      const res = await adminApi.credentials.verify(cred.credentialId);
      toast.success(`验证完成: ${res.status}`);
      await loadCredentials();
    } catch (e) {
      toast.error(isAppError(e) ? e.message : '验证失败');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setActionLoading(deleteTarget.credentialId + '_delete');
    try {
      await adminApi.credentials.delete(deleteTarget.credentialId);
      toast.success('凭据已删除');
      await loadCredentials();
    } catch (e) {
      toast.error(isAppError(e) ? e.message : '删除失败');
    } finally {
      setActionLoading(null);
      setDeleteTarget(null);
    }
  };

  function formatDate(iso?: string) {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' });
    } catch {
      return iso;
    }
  }

  return (
    <div className="page-enter">
      <PageHeader
        title="Provider 凭据"
        description="管理 AI Provider 的 API 凭据"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="gap-2" onClick={loadCredentials} disabled={loading}>
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
            <Button size="sm" className="gap-2" onClick={() => setCreateDialogOpen(true)}>
              <Plus className="w-3.5 h-3.5" />
              添加凭据
            </Button>
          </div>
        }
      />

      <Card className="card-glow">
        <CardContent className="p-0">
          {loading && (
            <div className="p-4">
              <LoadingRows count={3} />
            </div>
          )}

          {!loading && error && (
            <ErrorDisplay message={error} onRetry={loadCredentials} className="py-8" />
          )}

          {!loading && !error && credentials.length === 0 && (
            <EmptyState
              title="暂无凭据"
              description="添加 AI Provider 凭据以启用模型调用"
              icon={<Key className="w-6 h-6 text-muted-foreground" />}
              action={
                <Button size="sm" className="gap-2" onClick={() => setCreateDialogOpen(true)}>
                  <Plus className="w-3.5 h-3.5" />
                  添加凭据
                </Button>
              }
            />
          )}

          {!loading && !error && credentials.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>凭据 ID</TableHead>
                  <TableHead>Provider</TableHead>
                  <TableHead>名称</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>最近验证</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {credentials.map((cred) => (
                  <TableRow key={cred.credentialId}>
                    <TableCell>
                      <MonoText>{cred.credentialId}</MonoText>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm font-medium">{cred.provider}</span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">{cred.name || '—'}</span>
                    </TableCell>
                    <TableCell>
                      <StatusBadge variant={credStatusVariant(cred.status)}>
                        {cred.status === 'valid' ? (
                          <><CheckCircle2 className="w-3 h-3 mr-1 inline" />有效</>
                        ) : cred.status === 'invalid' ? (
                          <><AlertCircle className="w-3 h-3 mr-1 inline" />无效</>
                        ) : (
                          '未验证'
                        )}
                      </StatusBadge>
                    </TableCell>
                    <TableCell>
                      <span className="text-xs text-muted-foreground">{formatDate(cred.lastVerifiedAt)}</span>
                    </TableCell>
                    <TableCell>
                      <span className="text-xs text-muted-foreground">{formatDate(cred.createdAt)}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs gap-1"
                          disabled={actionLoading === cred.credentialId + '_verify'}
                          onClick={() => handleVerify(cred)}
                        >
                          {actionLoading === cred.credentialId + '_verify' ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <ShieldCheck className="w-3 h-3" />
                          )}
                          验证
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs gap-1 text-destructive hover:text-destructive"
                          disabled={actionLoading === cred.credentialId + '_delete'}
                          onClick={() => setDeleteTarget(cred)}
                        >
                          {actionLoading === cred.credentialId + '_delete' ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <Trash2 className="w-3 h-3" />
                          )}
                          删除
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <CreateCredentialDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onCreated={loadCredentials}
      />

      {deleteTarget && (
        <ConfirmDialog
          open={!!deleteTarget}
          onOpenChange={(open) => !open && setDeleteTarget(null)}
          title="删除凭据"
          description={`确认删除 ${deleteTarget.provider} 凭据「${deleteTarget.name || deleteTarget.credentialId}」吗？`}
          confirmLabel="删除"
          destructive
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
}

export default function AdminCredentialsPage() {
  return (
    <RequireAdmin>
      <AppShell>
        <AdminCredentialsContent />
      </AppShell>
    </RequireAdmin>
  );
}
