/**
 * Admin Invitation Detail Page - /admin/invitations/:invitationId
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Per Admin_后台信息架构与交互冻结.md §3.2 (v0.4)
 * Shows full invitation details, allows revoke and resend actions.
 */

import { useCallback, useEffect, useState } from 'react';
import { useParams, useLocation, Link } from 'wouter';
import { adminApi, AdminInvitation, isAppError } from '@/lib/api';
import { RequireAdmin } from '@/components/guards/RouteGuard';
import { AppShell } from '@/components/layout/AppShell';
import { StatusBadge, invitationStatusVariant } from '@/components/shared/StatusBadge';
import {
  PageHeader,
  ErrorDisplay,
  MonoText,
  InfoRow,
  ConfirmDialog,
} from '@/components/shared/PageComponents';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import {
  ArrowLeft,
  RefreshCw,
  XCircle,
  Send,
  Loader2,
  Mail,
  User,
  Building2,
  Shield,
  Clock,
  CheckCircle2,
  AlertCircle,
  Hash,
} from 'lucide-react';

function formatDate(iso?: string): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  } catch { return iso; }
}

function isExpired(iso: string): boolean {
  return new Date(iso) < new Date();
}

const STATUS_LABELS: Record<string, string> = {
  pending: '待使用',
  consumed: '已使用',
  revoked: '已撤销',
};

const ROLE_LABELS: Record<string, string> = {
  user: '普通用户',
  admin: '系统管理员',
  workspace_member: '工作区成员',
  workspace_admin: '工作区管理员',
};

function fallbackCopyToClipboard(text: string): void {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.left = '-9999px';
  textarea.style.top = '-9999px';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();

  try {
    document.execCommand('copy');
    toast.success('邀请链接已复制');
  } catch (err) {
    toast.error('复制失败，请手动复制链接');
    console.error('复制失败:', err);
  } finally {
    document.body.removeChild(textarea);
  }
}

function AdminInvitationDetailContent() {
  const { invitationId } = useParams<{ invitationId: string }>();
  const [, navigate] = useLocation();

  const [invitation, setInvitation] = useState<AdminInvitation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [revokeDialogOpen, setRevokeDialogOpen] = useState(false);

  const loadInvitation = useCallback(async () => {
    if (!invitationId) return;
    setLoading(true);
    setError(null);
    try {
      const inv = await adminApi.invitations.get(invitationId);
      setInvitation(inv);
    } catch (e) {
      setError(isAppError(e) ? e.message : '加载邀请详情失败');
    } finally {
      setLoading(false);
    }
  }, [invitationId]);

  useEffect(() => {
    loadInvitation();
  }, [loadInvitation]);

  const handleRevoke = async () => {
    if (!invitation) return;
    setActionLoading('revoke');
    try {
      await adminApi.invitations.revoke(invitation.invitationId);
      toast.success('邀请已撤销');
      await loadInvitation();
    } catch (e) {
      toast.error(isAppError(e) ? e.message : '撤销失败');
    } finally {
      setActionLoading(null);
      setRevokeDialogOpen(false);
    }
  };

  const handleResend = async () => {
    if (!invitation) return;
    setActionLoading('resend');
    try {
      await adminApi.invitations.resend(invitation.invitationId);
      toast.success('邀请邮件已重新发送');
    } catch (e) {
      toast.error(isAppError(e) ? e.message : '重发失败');
    } finally {
      setActionLoading(null);
    }
  };

  const handleCopyInviteLink = () => {
    if (!invitation) return;

    const inviteUrl = `${window.location.origin}/invite/${invitation.invitationId}`;

    // 方法1：尝试使用 Clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(inviteUrl).then(() => {
        toast.success('邀请链接已复制');
      }).catch(() => {
        // 方法2：使用传统方式作为后备
        fallbackCopyToClipboard(inviteUrl);
      });
    } else {
      // 方法2：使用传统方式
      fallbackCopyToClipboard(inviteUrl);
    }
  };

  const expired = invitation ? isExpired(invitation.expiresAt) : false;

  return (
    <div className="page-enter">
      <PageHeader
        title="邀请详情"
        description={invitationId}
        actions={
          <div className="flex items-center gap-2">
            <Link href="/admin/invitations">
              <Button variant="outline" size="sm" className="gap-2">
                <ArrowLeft className="w-3.5 h-3.5" />
                返回列表
              </Button>
            </Link>
            <Button variant="outline" size="sm" className="gap-2" onClick={loadInvitation} disabled={loading}>
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
          </div>
        }
      />

      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
        </div>
      )}

      {!loading && error && (
        <ErrorDisplay message={error} onRetry={loadInvitation} />
      )}

      {!loading && !error && invitation && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Main details */}
          <div className="lg:col-span-2 space-y-5">
            <Card className="card-glow">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2" style={{ fontFamily: 'Space Grotesk' }}>
                  <Mail className="w-4.5 h-4.5 text-primary" />
                  邀请信息
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-0">
                  <InfoRow
                    label="邀请 ID"
                    value={<MonoText>{invitation.invitationId}</MonoText>}
                  />
                  {invitation.loginUsername && (
                    <InfoRow
                      label="登录用户名"
                      value={
                        <div className="flex items-center gap-1.5">
                          <User className="w-3.5 h-3.5 text-muted-foreground" />
                          <span className="text-sm font-medium text-foreground">{invitation.loginUsername}</span>
                        </div>
                      }
                    />
                  )}
                  <InfoRow
                    label="目标邮箱"
                    value={
                      <div className="flex items-center gap-1.5">
                        <Mail className="w-3.5 h-3.5 text-muted-foreground" />
                        <span className="text-sm">{invitation.targetEmail}</span>
                      </div>
                    }
                  />
                  <InfoRow
                    label="工作区 ID"
                    value={
                      <div className="flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-muted-foreground" />
                        <MonoText>{invitation.workspaceId}</MonoText>
                      </div>
                    }
                  />
                  <InfoRow
                    label="角色"
                    value={
                      <div className="flex items-center gap-1.5">
                        <Shield className="w-3.5 h-3.5 text-muted-foreground" />
                        <StatusBadge variant={invitation.role === 'admin' ? 'info' : 'neutral'}>
                          {ROLE_LABELS[invitation.role] ?? invitation.role}
                        </StatusBadge>
                      </div>
                    }
                  />
                  <InfoRow
                    label="状态"
                    value={
                      <div className="flex items-center gap-2">
                        <StatusBadge variant={invitationStatusVariant(invitation.status)}>
                          {STATUS_LABELS[invitation.status] ?? invitation.status}
                        </StatusBadge>
                        {invitation.status === 'pending' && expired && (
                          <StatusBadge variant="warning">已过期</StatusBadge>
                        )}
                      </div>
                    }
                  />
                  <InfoRow
                    label="过期时间"
                    value={
                      <span className={`text-sm ${expired ? 'text-red-400' : 'text-foreground'}`}>
                        {formatDate(invitation.expiresAt)}
                        {expired && <span className="text-xs ml-1 text-red-400/70">（已过期）</span>}
                      </span>
                    }
                  />
                  <InfoRow
                    label="创建时间"
                    value={<span className="text-sm text-muted-foreground">{formatDate(invitation.createdAt)}</span>}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Consumption info */}
            {invitation.status === 'consumed' && (
              <Card className="card-glow border-green-500/20">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2" style={{ fontFamily: 'Space Grotesk' }}>
                    <CheckCircle2 className="w-4.5 h-4.5 text-green-400" />
                    接受信息
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-0">
                    {invitation.consumedAt && (
                      <InfoRow
                        label="接受时间"
                        value={<span className="text-sm">{formatDate(invitation.consumedAt)}</span>}
                      />
                    )}
                    {invitation.consumedByUserId && (
                      <InfoRow
                        label="接受用户 ID"
                        value={<MonoText>{invitation.consumedByUserId}</MonoText>}
                      />
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Error info */}
            {invitation.lastError && (
              <Card className="card-glow border-red-500/20">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2 text-red-400" style={{ fontFamily: 'Space Grotesk' }}>
                    <AlertCircle className="w-4.5 h-4.5" />
                    最近错误
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-red-400/80 font-mono">{invitation.lastError}</p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Actions sidebar */}
          <div className="space-y-4">
            <Card className="card-glow">
              <CardHeader className="pb-3">
                <CardTitle className="text-base" style={{ fontFamily: 'Space Grotesk' }}>
                  操作
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {invitation.status === 'pending' && (
                  <>
                    <Button
                      className="w-full gap-2"
                      variant="outline"
                      disabled={!!actionLoading}
                      onClick={handleResend}
                    >
                      {actionLoading === 'resend' ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                      重新发送邀请邮件
                    </Button>

                    <Button
                      className="w-full gap-2"
                      variant="outline"
                      disabled={!!actionLoading}
                      onClick={() => setRevokeDialogOpen(true)}
                    >
                      {actionLoading === 'revoke' ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <XCircle className="w-4 h-4 text-destructive" />
                      )}
                      <span className="text-destructive">撤销邀请</span>
                    </Button>
                  </>
                )}

                {invitation.status !== 'pending' && (
                  <div className="rounded-lg bg-muted/20 border border-border px-4 py-3">
                    <p className="text-xs text-muted-foreground">
                      此邀请已{STATUS_LABELS[invitation.status]}，无法执行操作。
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Invite link */}
            <Card className="card-glow">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground" style={{ fontFamily: 'Space Grotesk' }}>
                  邀请链接
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg bg-muted/20 border border-border p-3">
                  <p className="text-xs font-mono text-muted-foreground break-all">
                    {typeof window !== 'undefined' ? window.location.origin : ''}/invite/{invitation.invitationId}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mt-2 gap-2 text-xs"
                  onClick={handleCopyInviteLink}
                >
                  复制邀请链接
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Revoke confirm dialog */}
      {invitation && (
        <ConfirmDialog
          open={revokeDialogOpen}
          onOpenChange={setRevokeDialogOpen}
          title="撤销邀请"
          description={`确认撤销发给 ${invitation.loginUsername || invitation.targetEmail} 的邀请吗？此操作不可撤销。`}
          confirmLabel="撤销"
          destructive
          onConfirm={handleRevoke}
        />
      )}
    </div>
  );
}

export default function AdminInvitationDetailPage() {
  return (
    <RequireAdmin>
      <AppShell>
        <AdminInvitationDetailContent />
      </AppShell>
    </RequireAdmin>
  );
}
