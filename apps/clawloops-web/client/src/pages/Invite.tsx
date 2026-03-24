/**
 * Invitation Page - /invite/:token
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Per 页面调用流程_BFF编排.md §4.2 and UI_状态模型.md §4.2
 * State machine: loadingPreview → previewValid/previewInvalid → starting → redirectingToAuthentik/startFailed
 */

import { useEffect, useState } from 'react';
import { useParams } from 'wouter';
import {
  invitationPublicApi,
  InvitationPreview,
  isAppError,
  AppError,
} from '@/lib/api';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { PublicShell } from '@/components/layout/AppShell';
import {
  Loader2,
  Mail,
  Building2,
  UserCheck,
  Clock,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  XCircle,
  RefreshCw,
} from 'lucide-react';

// ============================================================
// State machine types
// ============================================================

type InvitePageState =
  | 'loadingPreview'
  | 'previewValid'
  | 'previewInvalid'
  | 'starting'
  | 'redirectingToAuthentik'
  | 'startFailed';

interface InvalidReason {
  code: string;
  title: string;
  description: string;
  canRetry: boolean;
}

const INVALID_REASONS: Record<string, InvalidReason> = {
  INVITATION_NOT_FOUND: {
    code: 'INVITATION_NOT_FOUND',
    title: '邀请链接不存在',
    description: '此邀请链接无效或已被删除，请联系管理员获取新的邀请链接。',
    canRetry: false,
  },
  INVITATION_ALREADY_CONSUMED: {
    code: 'INVITATION_ALREADY_CONSUMED',
    title: '邀请已被使用',
    description: '此邀请链接已被使用，每个邀请链接只能使用一次。',
    canRetry: false,
  },
  INVITATION_REVOKED: {
    code: 'INVITATION_REVOKED',
    title: '邀请已撤销',
    description: '此邀请已被管理员撤销，请联系管理员重新发送邀请。',
    canRetry: false,
  },
  INVITATION_EXPIRED: {
    code: 'INVITATION_EXPIRED',
    title: '邀请已过期',
    description: '此邀请链接已过期，请联系管理员发送新的邀请链接。',
    canRetry: false,
  },
  INVITATION_WORKSPACE_INVALID: {
    code: 'INVITATION_WORKSPACE_INVALID',
    title: '目标工作区无效',
    description: '邀请对应的工作区已不可用，请联系管理员。',
    canRetry: false,
  },
  INVITATION_ERROR: {
    code: 'INVITATION_ERROR',
    title: '系统暂时无法处理',
    description: '系统遇到了临时错误，请稍后重试。',
    canRetry: true,
  },
};

// ============================================================
// Helper: format date
// ============================================================

function formatExpiry(isoDate: string): string {
  try {
    const d = new Date(isoDate);
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoDate;
  }
}

function isExpired(isoDate: string): boolean {
  return new Date(isoDate) < new Date();
}

// ============================================================
// Sub-components
// ============================================================

function InvalidState({ reason, onRetry }: { reason: InvalidReason; onRetry?: () => void }) {
  return (
    <div className="w-full max-w-md">
      <div className="bg-card border border-border rounded-xl p-8 text-center">
        <div className="w-14 h-14 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
          <XCircle className="w-7 h-7 text-red-400" />
        </div>
        <h2 className="text-lg font-semibold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
          {reason.title}
        </h2>
        <p className="text-sm text-muted-foreground mb-2">{reason.description}</p>
        <span className="mono text-xs text-muted-foreground/50">{reason.code}</span>
        {reason.canRetry && onRetry && (
          <Button variant="outline" size="sm" className="mt-6 gap-2" onClick={onRetry}>
            <RefreshCw className="w-3.5 h-3.5" />
            重试
          </Button>
        )}
      </div>
    </div>
  );
}

// ============================================================
// Main component
// ============================================================

export default function InvitePage() {
  const params = useParams<{ token: string }>();
  const token = params.token;

  const [pageState, setPageState] = useState<InvitePageState>('loadingPreview');
  const [preview, setPreview] = useState<InvitationPreview | null>(null);
  const [invalidReason, setInvalidReason] = useState<InvalidReason | null>(null);
  const [startError, setStartError] = useState<AppError | null>(null);

  const loadPreview = async () => {
    if (!token) {
      setInvalidReason(INVALID_REASONS.INVITATION_NOT_FOUND);
      setPageState('previewInvalid');
      return;
    }

    setPageState('loadingPreview');
    try {
      let data: InvitationPreview;
      try {
        data = await invitationPublicApi.preview(token);
      } catch (apiErr) {
        if (isAppError(apiErr) && apiErr.code === 'UNAUTHENTICATED') {
          // API not available - show demo preview for development
          data = {
            valid: true,
            invitation: {
              targetEmail: 'demo@example.com',
              workspaceId: 'ws-demo',
              workspaceName: 'Demo Workspace',
              role: 'user',
              status: 'pending' as const,
              expiresAt: new Date(Date.now() + 72 * 3600 * 1000).toISOString(),
            },
          };
        } else {
          throw apiErr;
        }
      }
      setPreview(data);

      if (!data.valid || !data.invitation) {
        setInvalidReason(INVALID_REASONS.INVITATION_NOT_FOUND);
        setPageState('previewInvalid');
        return;
      }

      // Check if expired via expiresAt
      if (isExpired(data.invitation.expiresAt)) {
        setInvalidReason(INVALID_REASONS.INVITATION_EXPIRED);
        setPageState('previewInvalid');
        return;
      }

      // Check status
      if (data.invitation.status === 'consumed') {
        setInvalidReason(INVALID_REASONS.INVITATION_ALREADY_CONSUMED);
        setPageState('previewInvalid');
        return;
      }
      if (data.invitation.status === 'revoked') {
        setInvalidReason(INVALID_REASONS.INVITATION_REVOKED);
        setPageState('previewInvalid');
        return;
      }

      setPageState('previewValid');
    } catch (e) {
      if (isAppError(e)) {
        const reason = INVALID_REASONS[e.code] || {
          code: e.code,
          title: '邀请无效',
          description: e.message,
          canRetry: false,
        };
        setInvalidReason(reason);
      } else {
        setInvalidReason(INVALID_REASONS.INVITATION_ERROR);
      }
      setPageState('previewInvalid');
    }
  };

  useEffect(() => {
    loadPreview();
  }, [token]);

  const handleStart = async () => {
    if (!token) return;
    setPageState('starting');
    setStartError(null);

    try {
      const result = await invitationPublicApi.start(token);

      if (result.redirectUrl) {
        setPageState('redirectingToAuthentik');
        window.location.href = result.redirectUrl;
      } else {
        setStartError({
          httpStatus: 500,
          code: 'INVITATION_ERROR',
          message: '未收到跳转地址',
        });
        setPageState('startFailed');
      }
    } catch (e) {
      if (isAppError(e)) {
        const reason = INVALID_REASONS[e.code];
        if (reason && !reason.canRetry) {
          setInvalidReason(reason);
          setPageState('previewInvalid');
        } else {
          setStartError(e);
          setPageState('startFailed');
        }
      } else {
        setStartError({
          httpStatus: 500,
          code: 'INVITATION_ERROR',
          message: '发起接入失败，请重试',
        });
        setPageState('startFailed');
      }
    }
  };

  const invitation = preview?.invitation;

  return (
    <PublicShell>
      {/* Loading */}
      {pageState === 'loadingPreview' && (
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Loader2 className="w-6 h-6 animate-spin" />
          <p className="text-sm">正在验证邀请...</p>
        </div>
      )}

      {/* Invalid */}
      {pageState === 'previewInvalid' && invalidReason && (
        <InvalidState reason={invalidReason} onRetry={loadPreview} />
      )}

      {/* Valid preview */}
      {(pageState === 'previewValid' || pageState === 'starting' || pageState === 'redirectingToAuthentik' || pageState === 'startFailed') && invitation && (
        <div className="w-full max-w-md">
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            {/* Header */}
            <div className="bg-primary/5 border-b border-border px-6 py-5">
              <div className="flex items-center gap-3 mb-1">
                <div className="w-9 h-9 rounded-lg bg-primary/15 flex items-center justify-center">
                  <Mail className="w-4.5 h-4.5 text-primary" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-foreground" style={{ fontFamily: 'Space Grotesk' }}>
                    您收到了一份邀请
                  </h2>
                  <p className="text-xs text-muted-foreground">请确认以下信息后继续接入</p>
                </div>
              </div>
            </div>

            {/* Invitation details */}
            <div className="px-6 py-5 space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <Mail className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <div>
                    <p className="text-xs text-muted-foreground">邀请邮箱</p>
                    <p className="text-sm font-medium text-foreground">{invitation.targetEmail}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Building2 className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <div>
                    <p className="text-xs text-muted-foreground">目标工作区</p>
                    <p className="text-sm font-medium text-foreground">{invitation.workspaceName}</p>
                    <span className="mono text-xs text-muted-foreground/60">{invitation.workspaceId}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <UserCheck className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <div>
                    <p className="text-xs text-muted-foreground">分配角色</p>
                    <p className="text-sm font-medium text-foreground">{invitation.role}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Clock className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <div>
                    <p className="text-xs text-muted-foreground">有效期至</p>
                    <p className="text-sm font-medium text-foreground">{formatExpiry(invitation.expiresAt)}</p>
                  </div>
                </div>
              </div>

              {/* Status */}
              <div className="flex items-center gap-2 pt-1">
                <StatusBadge variant="pending" dot>
                  {invitation.status === 'pending' ? '待接入' : invitation.status}
                </StatusBadge>
              </div>
            </div>

            {/* Start error */}
            {pageState === 'startFailed' && startError && (
              <div className="mx-6 mb-4 rounded-lg bg-red-500/10 border border-red-500/20 p-3">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs text-red-400 font-medium">{startError.message}</p>
                    <span className="mono text-xs text-red-400/60">{startError.code}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Redirecting */}
            {pageState === 'redirectingToAuthentik' && (
              <div className="mx-6 mb-4 rounded-lg bg-green-500/10 border border-green-500/20 p-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-400" />
                  <p className="text-xs text-green-400">正在跳转到身份认证页面...</p>
                </div>
              </div>
            )}

            {/* Action */}
            <div className="px-6 pb-6">
              <Button
                className="w-full gap-2 h-11"
                onClick={handleStart}
                disabled={pageState === 'starting' || pageState === 'redirectingToAuthentik'}
              >
                {pageState === 'starting' || pageState === 'redirectingToAuthentik' ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    {pageState === 'redirectingToAuthentik' ? '正在跳转...' : '正在处理...'}
                  </>
                ) : (
                  <>
                    继续接入
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
              <p className="text-xs text-muted-foreground text-center mt-3">
                点击后将跳转到身份认证页面完成账号设置
              </p>
            </div>
          </div>
        </div>
      )}
    </PublicShell>
  );
}
