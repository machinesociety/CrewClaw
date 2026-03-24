/**
 * PostLogin Page - /post-login
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Per 页面调用流程_BFF编排.md §4.3 and UI_状态模型.md §4.3
 * State machine: initializing → callingPostLogin → postLoginSucceeded/workspaceMissing/postLoginFailed
 *
 * This page is called AFTER Authentik login completes.
 * Frontend actively calls POST /api/v1/auth/post-login (idempotent).
 */

import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { authApi, PostLoginResult, isAppError, AppError } from '@/lib/api';
import { PublicShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/button';
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  XCircle,
  Info,
} from 'lucide-react';

// ============================================================
// State machine
// ============================================================

type PostLoginState =
  | 'initializing'
  | 'callingPostLogin'
  | 'postLoginSucceeded'
  | 'workspaceMissing'
  | 'needsWorkspaceSelection'
  | 'postLoginFailed';

interface ErrorInfo {
  code: string;
  title: string;
  description: string;
  canRetry: boolean;
}

const ERROR_MAP: Record<string, ErrorInfo> = {
  INVITATION_EMAIL_MISMATCH: {
    code: 'INVITATION_EMAIL_MISMATCH',
    title: '邮箱不匹配',
    description: '当前登录账号的邮箱与邀请目标邮箱不一致，无法完成接入。请使用正确的邮箱账号登录。',
    canRetry: false,
  },
  INVITATION_REVOKED: {
    code: 'INVITATION_REVOKED',
    title: '邀请已失效',
    description: '此邀请已被管理员撤销，请联系管理员重新发送邀请。',
    canRetry: false,
  },
  INVITATION_ALREADY_CONSUMED: {
    code: 'INVITATION_ALREADY_CONSUMED',
    title: '邀请已被使用',
    description: '此邀请已被消费，但您可以继续完成登录收口。',
    canRetry: true,
  },
  INVITATION_EXPIRED: {
    code: 'INVITATION_EXPIRED',
    title: '邀请已过期',
    description: '此邀请链接已过期，请联系管理员发送新的邀请。',
    canRetry: false,
  },
  INVITATION_WORKSPACE_INVALID: {
    code: 'INVITATION_WORKSPACE_INVALID',
    title: '目标工作区不可用',
    description: '邀请对应的工作区已不可用，请联系管理员。',
    canRetry: false,
  },
  USER_SYNC_ERROR: {
    code: 'USER_SYNC_ERROR',
    title: '登录收口失败',
    description: '登录成功但用户信息同步失败，请重试。如问题持续，请联系管理员。',
    canRetry: true,
  },
  USER_DISABLED: {
    code: 'USER_DISABLED',
    title: '账号已禁用',
    description: '您的账号已被管理员禁用，无法访问平台。请联系管理员。',
    canRetry: false,
  },
  INVITATION_ERROR: {
    code: 'INVITATION_ERROR',
    title: '接入流程执行失败',
    description: '系统遇到了错误，请重试。如问题持续，请联系管理员。',
    canRetry: true,
  },
};

// ============================================================
// Main component
// ============================================================

export default function PostLoginPage() {
  const [, navigate] = useLocation();
  const [pageState, setPageState] = useState<PostLoginState>('initializing');
  const [error, setError] = useState<ErrorInfo | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const callPostLogin = async () => {
    setPageState('callingPostLogin');
    setError(null);

    try {
      const result: PostLoginResult = await authApi.postLogin();

      // Determine next step based on result
      const hasWorkspace = result.hasWorkspace ?? (result.redirectTo === '/workspace-entry');
      const needsSelection = result.needsWorkspaceSelection ?? false;

      if (hasWorkspace) {
        setPageState('postLoginSucceeded');
        // Navigate to workspace-entry
        setTimeout(() => {
          navigate('/workspace-entry');
        }, 800);
      } else {
        setPageState('workspaceMissing');
      }
    } catch (e) {
      if (isAppError(e)) {
        const errInfo = ERROR_MAP[e.code] || {
          code: e.code,
          title: '登录收口失败',
          description: e.message,
          canRetry: true,
        };
        setError(errInfo);
      } else {
        setError({
          code: 'UNKNOWN_ERROR',
          title: '未知错误',
          description: '发生了未知错误，请重试。',
          canRetry: true,
        });
      }
      setPageState('postLoginFailed');
    }
  };

  useEffect(() => {
    // Auto-call post-login on mount
    callPostLogin();
  }, [retryCount]);

  const handleRetry = () => {
    setRetryCount((c) => c + 1);
  };

  return (
    <PublicShell>
      <div className="w-full max-w-sm">
        <div className="bg-card border border-border rounded-xl p-8 text-center">

          {/* Initializing / Calling */}
          {(pageState === 'initializing' || pageState === 'callingPostLogin') && (
            <>
              <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-5">
                <Loader2 className="w-7 h-7 text-primary animate-spin" />
              </div>
              <h2 className="text-lg font-semibold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
                正在完成登录
              </h2>
              <p className="text-sm text-muted-foreground">
                请稍候，系统正在完成身份绑定...
              </p>
            </>
          )}

          {/* Success */}
          {pageState === 'postLoginSucceeded' && (
            <>
              <div className="w-14 h-14 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-5">
                <CheckCircle2 className="w-7 h-7 text-green-400" />
              </div>
              <h2 className="text-lg font-semibold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
                登录成功
              </h2>
              <p className="text-sm text-muted-foreground">
                正在跳转到工作区入口...
              </p>
            </>
          )}

          {/* No workspace */}
          {pageState === 'workspaceMissing' && (
            <>
              <div className="w-14 h-14 rounded-full bg-yellow-500/10 flex items-center justify-center mx-auto mb-5">
                <Info className="w-7 h-7 text-yellow-400" />
              </div>
              <h2 className="text-lg font-semibold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
                暂无可用工作区
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                您的账号尚未绑定工作区，请联系管理员为您分配工作区。
              </p>
              <Button variant="outline" size="sm" onClick={() => navigate('/login')}>
                返回登录页
              </Button>
            </>
          )}

          {/* Failed */}
          {pageState === 'postLoginFailed' && error && (
            <>
              <div className="w-14 h-14 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-5">
                {error.canRetry ? (
                  <AlertCircle className="w-7 h-7 text-red-400" />
                ) : (
                  <XCircle className="w-7 h-7 text-red-400" />
                )}
              </div>
              <h2 className="text-lg font-semibold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
                {error.title}
              </h2>
              <p className="text-sm text-muted-foreground mb-1">{error.description}</p>
              <span className="mono text-xs text-muted-foreground/50">{error.code}</span>

              <div className="flex gap-2 justify-center mt-6">
                {error.canRetry && (
                  <Button size="sm" className="gap-2" onClick={handleRetry}>
                    <RefreshCw className="w-3.5 h-3.5" />
                    重试
                  </Button>
                )}
                <Button variant="outline" size="sm" onClick={() => navigate('/login')}>
                  返回登录
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </PublicShell>
  );
}
