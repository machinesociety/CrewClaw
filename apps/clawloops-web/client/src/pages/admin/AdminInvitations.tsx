/**
 * Admin Invitations Page - /admin/invitations
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Per 页面调用流程_BFF编排.md §6.3
 * List invitations, create new, revoke, resend
 */

import { useCallback, useEffect, useState } from 'react';
import {
  adminApi,
  AdminInvitation,
  CreateInvitationRequest,
  isAppError,
} from '@/lib/api';
import { RequireAdmin } from '@/components/guards/RouteGuard';
import { AppShell } from '@/components/layout/AppShell';
import {
  StatusBadge,
  invitationStatusVariant,
} from '@/components/shared/StatusBadge';
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
  XCircle,
  Send,
  Mail,
  Loader2,
} from 'lucide-react';

// ============================================================
// Create Invitation Dialog
// ============================================================

interface CreateDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onCreated: () => void;
}

function CreateInvitationDialog({ open, onOpenChange, onCreated }: CreateDialogProps) {
  const [form, setForm] = useState<CreateInvitationRequest>({
    targetEmail: '',
    workspaceId: '',
    role: 'user',
    expiresInHours: 72,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.targetEmail || !form.workspaceId) {
      setError('邮箱和工作区 ID 为必填项');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await adminApi.invitations.create(form);
      toast.success('邀请已创建');
      onCreated();
      onOpenChange(false);
      setForm({ targetEmail: '', workspaceId: '', role: 'user', expiresInHours: 72 });
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
          <DialogTitle>创建邀请</DialogTitle>
          <DialogDescription>
            向指定邮箱发送工作区接入邀请
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">目标邮箱 *</Label>
            <Input
              id="email"
              type="email"
              placeholder="user@example.com"
              value={form.targetEmail}
              onChange={(e) => setForm((f) => ({ ...f, targetEmail: e.target.value }))}
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="workspaceId">工作区 ID *</Label>
            <Input
              id="workspaceId"
              placeholder="ws-xxxxxxxx"
              value={form.workspaceId}
              onChange={(e) => setForm((f) => ({ ...f, workspaceId: e.target.value }))}
              required
              className="mono"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="role">角色</Label>
            <Select
              value={form.role}
              onValueChange={(v) => setForm((f) => ({ ...f, role: v }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="user">user</SelectItem>
                <SelectItem value="admin">admin</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="expires">有效期（小时）</Label>
            <Select
              value={String(form.expiresInHours)}
              onValueChange={(v) => setForm((f) => ({ ...f, expiresInHours: Number(v) }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="24">24 小时</SelectItem>
                <SelectItem value="48">48 小时</SelectItem>
                <SelectItem value="72">72 小时（默认）</SelectItem>
                <SelectItem value="168">7 天</SelectItem>
                <SelectItem value="720">30 天</SelectItem>
              </SelectContent>
            </Select>
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
              创建邀请
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================
// Main Page
// ============================================================

function AdminInvitationsContent() {
  const [invitations, setInvitations] = useState<AdminInvitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState<AdminInvitation | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadInvitations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminApi.invitations.list();
      setInvitations(res.invitations || []);
    } catch (e) {
      setError(isAppError(e) ? e.message : '加载邀请列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInvitations();
  }, [loadInvitations]);

  const handleRevoke = async () => {
    if (!revokeTarget) return;
    setActionLoading(revokeTarget.invitationId);
    try {
      await adminApi.invitations.revoke(revokeTarget.invitationId);
      toast.success('邀请已撤销');
      await loadInvitations();
    } catch (e) {
      toast.error(isAppError(e) ? e.message : '撤销失败');
    } finally {
      setActionLoading(null);
      setRevokeTarget(null);
    }
  };

  const handleResend = async (inv: AdminInvitation) => {
    setActionLoading(inv.invitationId + '_resend');
    try {
      await adminApi.invitations.resend(inv.invitationId);
      toast.success('邀请邮件已重新发送');
    } catch (e) {
      toast.error(isAppError(e) ? e.message : '重发失败');
    } finally {
      setActionLoading(null);
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

  function isExpired(iso: string) {
    return new Date(iso) < new Date();
  }

  return (
    <div className="page-enter">
      <PageHeader
        title="邀请管理"
        description="管理平台用户邀请"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="gap-2" onClick={loadInvitations} disabled={loading}>
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
            <Button size="sm" className="gap-2" onClick={() => setCreateDialogOpen(true)}>
              <Plus className="w-3.5 h-3.5" />
              创建邀请
            </Button>
          </div>
        }
      />

      <Card className="card-glow">
        <CardContent className="p-0">
          {loading && (
            <div className="p-4">
              <LoadingRows count={5} />
            </div>
          )}

          {!loading && error && (
            <ErrorDisplay message={error} onRetry={loadInvitations} className="py-8" />
          )}

          {!loading && !error && invitations.length === 0 && (
            <EmptyState
              title="暂无邀请"
              description="点击「创建邀请」向用户发送邀请"
              icon={<Mail className="w-6 h-6 text-muted-foreground" />}
              action={
                <Button size="sm" className="gap-2" onClick={() => setCreateDialogOpen(true)}>
                  <Plus className="w-3.5 h-3.5" />
                  创建邀请
                </Button>
              }
            />
          )}

          {!loading && !error && invitations.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>邀请 ID</TableHead>
                  <TableHead>目标邮箱</TableHead>
                  <TableHead>工作区 ID</TableHead>
                  <TableHead>角色</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>过期时间</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invitations.map((inv) => (
                  <TableRow key={inv.invitationId}>
                    <TableCell>
                      <MonoText>{inv.invitationId}</MonoText>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{inv.targetEmail}</span>
                    </TableCell>
                    <TableCell>
                      <MonoText>{inv.workspaceId}</MonoText>
                    </TableCell>
                    <TableCell>
                      <StatusBadge variant={inv.role === 'admin' ? 'info' : 'neutral'}>
                        {inv.role}
                      </StatusBadge>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        <StatusBadge variant={invitationStatusVariant(inv.status)}>
                          {inv.status === 'pending' ? '待使用' : inv.status === 'consumed' ? '已使用' : '已撤销'}
                        </StatusBadge>
                        {inv.status === 'pending' && isExpired(inv.expiresAt) && (
                          <StatusBadge variant="warning">已过期</StatusBadge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={`text-xs ${isExpired(inv.expiresAt) ? 'text-red-400/70' : 'text-muted-foreground'}`}>
                        {formatDate(inv.expiresAt)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-xs text-muted-foreground">{formatDate(inv.createdAt)}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {inv.status === 'pending' && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs gap-1"
                              disabled={actionLoading === inv.invitationId + '_resend'}
                              onClick={() => handleResend(inv)}
                            >
                              {actionLoading === inv.invitationId + '_resend' ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : (
                                <Send className="w-3 h-3" />
                              )}
                              重发
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs gap-1 text-destructive hover:text-destructive"
                              disabled={actionLoading === inv.invitationId}
                              onClick={() => setRevokeTarget(inv)}
                            >
                              {actionLoading === inv.invitationId ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : (
                                <XCircle className="w-3 h-3" />
                              )}
                              撤销
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <CreateInvitationDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onCreated={loadInvitations}
      />

      {revokeTarget && (
        <ConfirmDialog
          open={!!revokeTarget}
          onOpenChange={(open) => !open && setRevokeTarget(null)}
          title="撤销邀请"
          description={`确认撤销发给 ${revokeTarget.targetEmail} 的邀请吗？此操作不可撤销。`}
          confirmLabel="撤销"
          destructive
          onConfirm={handleRevoke}
        />
      )}
    </div>
  );
}

export default function AdminInvitationsPage() {
  return (
    <RequireAdmin>
      <AppShell>
        <AdminInvitationsContent />
      </AppShell>
    </RequireAdmin>
  );
}
