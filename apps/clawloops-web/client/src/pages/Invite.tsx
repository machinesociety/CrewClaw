/**
 * Invitation Onboarding Page - /invite/:token
 * Design: Crafted Dark - ClawLoops Platform
 *
 * v0.5 (轻量认证修订):
 * - In-page accept: username + password + confirm → POST /public/invitations/{token}/accept
 * - No Authentik redirect, no /start, no external IAM
 * - loginUsername shown as primary display (proxy email hidden)
 * - Error handling per 页面调用流程_BFF编排.md §4.3:
 *   - INVITATION_NOT_FOUND / INVITATION_EXPIRED / INVITATION_REVOKED / INVITATION_ALREADY_CONSUMED → invalid page
 *   - INVITATION_USERNAME_MISMATCH → highlight username field
 *   - INVITATION_PASSWORD_INVALID → show password rules
 * - accepted=true + replayed=true → treat as success (no extra error)
 * - On success: navigate to /app
 */

import { useEffect, useState } from 'react';
import { useParams, useLocation } from 'wouter';
import {
  invitationPublicApi,
  authApi,
  InvitationPreview,
  PasswordPolicy,
  isAppError,
  getErrorCode,
} from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  Loader2, AlertCircle, CheckCircle2, Eye, EyeOff,
  Lock, User, Calendar, Briefcase, ShieldCheck, XCircle, Clock,
} from 'lucide-react';

// ============================================================
// State Machine
// ============================================================

type InvitePageState =
  | 'loadingPreview'
  | 'previewValid'        // invitation valid, show accept form
  | 'previewInvalid'      // invitation not found / expired / revoked / consumed
  | 'submitting'          // POST /accept in progress
  | 'accepted';           // success (including replayed=true)

interface FormErrors {
  username?: string;
  password?: string;
  passwordConfirm?: string;
  general?: string;
}

// ============================================================
// Helpers
// ============================================================

function formatExpiry(expiresAt: string): string {
  try {
    const d = new Date(expiresAt);
    const now = new Date();
    
    // 转换为北京时间（UTC+8）
    const getBeijingTime = (date: Date) => {
      const utc = date.getTime();
      return new Date(utc + 8 * 60 * 60 * 1000);
    };
    
    const dBeijing = getBeijingTime(d);
    const nowBeijing = getBeijingTime(now);
    
    // 计算时间差（毫秒）
    const diffMs = dBeijing.getTime() - nowBeijing.getTime();
    const diffH = Math.floor(diffMs / (1000 * 60 * 60));
    const diffD = Math.floor(diffH / 24);
    if (diffMs < 0) return '已过期';
    if (diffD > 0) return `${diffD} 天后过期`;
    if (diffH > 0) return `${diffH} 小时后过期`;
    return '即将过期';
  } catch {
    return expiresAt;
  }
}

function isProxyEmail(email: string): boolean {
  return (
    email.endsWith('.noemail.local') ||
    email.endsWith('.placeholder.local') ||
    email.includes('+noreply') ||
    email.startsWith('noreply')
  );
}

function roleLabel(role: string): string {
  const map: Record<string, string> = {
    member: '成员',
    workspace_member: '工作区成员',
    admin: '管理员',
    workspace_admin: '工作区管理员',
    viewer: '查看者',
    editor: '编辑者',
    user: '普通用户',
  };
  return map[role] ?? role;
}

function getInvalidReason(code: string): string {
  switch (code) {
    case 'INVITATION_NOT_FOUND': return '邀请链接不存在或已失效，请向管理员确认链接是否正确。';
    case 'INVITATION_EXPIRED': return '邀请链接已过期，请联系管理员重新发送邀请。';
    case 'INVITATION_REVOKED': return '邀请链接已被管理员撤销，请联系管理员重新发起邀请。';
    case 'INVITATION_ALREADY_CONSUMED': return '该邀请链接已被使用，每个链接只能使用一次。如有疑问请联系管理员。';
    default: return '邀请链接无效，请联系管理员获取新的邀请链接。';
  }
}

// ============================================================
// Component
// ============================================================

export default function InvitePage() {
  const { token } = useParams<{ token: string }>();
  const [, navigate] = useLocation();

  const [pageState, setPageState] = useState<InvitePageState>('loadingPreview');
  const [preview, setPreview] = useState<InvitationPreview['invitation'] | null>(null);
  const [invalidCode, setInvalidCode] = useState<string>('INVITATION_NOT_FOUND');
  const [policy, setPolicy] = useState<PasswordPolicy | null>(null);

  // Form state
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [formErrors, setFormErrors] = useState<FormErrors>({});

  // Load preview and password policy in parallel
  useEffect(() => {
    if (!token) {
      setInvalidCode('INVITATION_NOT_FOUND');
      setPageState('previewInvalid');
      return;
    }

    let cancelled = false;

    Promise.allSettled([
      invitationPublicApi.preview(token),
      authApi.options(),
    ]).then(([previewResult, optionsResult]) => {
      if (cancelled) return;

      // Handle password policy
      if (optionsResult.status === 'fulfilled' && optionsResult.value.passwordPolicy) {
        setPolicy(optionsResult.value.passwordPolicy);
      }

      // Handle preview
      if (previewResult.status === 'rejected') {
        const code = getErrorCode(previewResult.reason);
        setInvalidCode(code);
        setPageState('previewInvalid');
        return;
      }

      const data = previewResult.value;
      if (!data.valid || !data.invitation) {
        setInvalidCode('INVITATION_NOT_FOUND');
        setPageState('previewInvalid');
        return;
      }

      // Check status
      if (data.invitation.status === 'consumed') {
        setInvalidCode('INVITATION_ALREADY_CONSUMED');
        setPageState('previewInvalid');
        return;
      }
      if (data.invitation.status === 'revoked') {
        setInvalidCode('INVITATION_REVOKED');
        setPageState('previewInvalid');
        return;
      }

      setPreview(data.invitation);
      // Pre-fill username from loginUsername if available
      if (data.invitation.loginUsername) {
        setUsername(data.invitation.loginUsername);
      }
      setPageState('previewValid');
    });

    return () => { cancelled = true; };
  }, [token]);

  const buildPolicyHints = (): string[] => {
    if (!policy) return [];
    const hints: string[] = [];
    if (policy.minLength) hints.push(`至少 ${policy.minLength} 个字符`);
    if (policy.maxLength) hints.push(`最多 ${policy.maxLength} 个字符`);
    if (policy.requireLetter) hints.push('包含字母');
    if (policy.requireNumber) hints.push('包含数字');
    if (policy.disallowUsernameAsPassword) hints.push('不能与用户名相同');
    return hints;
  };

  const validate = (): boolean => {
    const errors: FormErrors = {};
    if (!username.trim()) errors.username = '请输入用户名';
    if (!password) {
      errors.password = '请输入密码';
    } else if (policy?.minLength && password.length < policy.minLength) {
      errors.password = `密码至少需要 ${policy.minLength} 个字符`;
    }
    if (!passwordConfirm) {
      errors.passwordConfirm = '请再次输入密码';
    } else if (password && passwordConfirm !== password) {
      errors.passwordConfirm = '两次输入的密码不一致';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleAccept = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !validate()) return;

    setPageState('submitting');
    setFormErrors({});

    try {
      const result = await invitationPublicApi.accept(token, {
        username: username.trim(),
        password,
        passwordConfirm,
      });

      // accepted=true (including replayed=true) → success
      if (result.accepted) {
        setPageState('accepted');
        setTimeout(() => {
          navigate(result.redirectTo ?? '/app');
        }, 1500);
      } else {
        setPageState('previewValid');
        setFormErrors({ general: '接入失败，请稍后重试' });
      }
    } catch (e) {
      setPageState('previewValid');
      const code = getErrorCode(e);

      if (
        code === 'INVITATION_NOT_FOUND' ||
        code === 'INVITATION_EXPIRED' ||
        code === 'INVITATION_REVOKED' ||
        code === 'INVITATION_ALREADY_CONSUMED'
      ) {
        setInvalidCode(code);
        setPageState('previewInvalid');
      } else if (code === 'INVITATION_USERNAME_MISMATCH') {
        setFormErrors({ username: '请使用管理员提供的用户名完成接入' });
      } else if (code === 'INVITATION_PASSWORD_INVALID') {
        const hints = buildPolicyHints();
        setFormErrors({
          password: hints.length > 0
            ? `密码不符合要求：${hints.join('、')}`
            : '密码不符合要求，请检查后重试',
        });
      } else if (isAppError(e) && e.httpStatus === 400) {
        setFormErrors({ general: e.message || '请求无效，请检查输入' });
      } else {
        setFormErrors({ general: '接入失败，请稍后重试' });
      }
    }
  };

  // ============================================================
  // Render: Loading
  // ============================================================

  if (pageState === 'loadingPreview') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
              <span className="text-primary font-bold text-sm" style={{ fontFamily: 'Space Grotesk' }}>CL</span>
            </div>
            <span className="text-foreground font-semibold text-lg" style={{ fontFamily: 'Space Grotesk' }}>ClawLoops</span>
          </div>
          <Loader2 className="w-5 h-5 text-muted-foreground animate-spin" />
          <p className="text-muted-foreground text-sm">正在验证邀请链接...</p>
        </div>
      </div>
    );
  }

  // ============================================================
  // Render: Invalid invitation
  // ============================================================

  if (pageState === 'previewInvalid') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="w-full max-w-md space-y-8 text-center">
          <div className="flex items-center gap-3 justify-center">
            <div className="w-10 h-10 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center">
              <span className="text-primary font-bold text-base" style={{ fontFamily: 'Space Grotesk' }}>CL</span>
            </div>
            <span className="text-foreground font-bold text-xl" style={{ fontFamily: 'Space Grotesk' }}>ClawLoops</span>
          </div>

          <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-8 space-y-4">
            <XCircle className="w-12 h-12 text-destructive mx-auto" />
            <div>
              <h2 className="text-xl font-bold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
                邀请链接无效
              </h2>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {getInvalidReason(invalidCode)}
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <Button variant="outline" className="w-full" onClick={() => navigate('/login')}>
              返回登录
            </Button>
            <p className="text-muted-foreground/50 text-xs">
              如有疑问，请联系系统管理员重新发送邀请
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ============================================================
  // Render: Success
  // ============================================================

  if (pageState === 'accepted') {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="w-full max-w-md space-y-8 text-center">
          <div className="flex items-center gap-3 justify-center">
            <div className="w-10 h-10 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center">
              <span className="text-primary font-bold text-base" style={{ fontFamily: 'Space Grotesk' }}>CL</span>
            </div>
            <span className="text-foreground font-bold text-xl" style={{ fontFamily: 'Space Grotesk' }}>ClawLoops</span>
          </div>

          <div className="rounded-xl border border-green-500/30 bg-green-500/10 p-8 space-y-4">
            <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto" />
            <div>
              <h2 className="text-xl font-bold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
                接入成功！
              </h2>
              <p className="text-muted-foreground text-sm">
                您已成功加入 <span className="text-foreground font-medium">{preview?.workspaceName}</span>
              </p>
              <p className="text-muted-foreground/60 text-xs mt-2">
                正在跳转到工作台...
              </p>
            </div>
          </div>

          <div className="flex items-center justify-center gap-2 text-muted-foreground text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>正在跳转...</span>
          </div>
        </div>
      </div>
    );
  }

  // ============================================================
  // Render: Accept form (previewValid | submitting)
  // ============================================================

  const inv = preview!;
  const showEmail = inv.targetEmail && !isProxyEmail(inv.targetEmail) && !inv.loginUsername;
  const policyHints = buildPolicyHints();
  const isBusy = pageState === 'submitting';

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-8">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center">
            <span className="text-primary font-bold text-base" style={{ fontFamily: 'Space Grotesk' }}>CL</span>
          </div>
          <span className="text-foreground font-bold text-xl" style={{ fontFamily: 'Space Grotesk' }}>ClawLoops</span>
        </div>

        {/* Invitation info card */}
        <div className="rounded-xl border border-border/60 bg-card p-6 space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-lg font-bold text-foreground" style={{ fontFamily: 'Space Grotesk' }}>
                您收到了一份邀请
              </h2>
              <p className="text-muted-foreground text-sm mt-0.5">
                完成设置后即可加入工作区
              </p>
            </div>
            <Badge variant="outline" className="border-green-500/40 text-green-400 bg-green-500/10 flex-shrink-0">
              <ShieldCheck className="w-3 h-3 mr-1" />
              有效
            </Badge>
          </div>

          <div className="space-y-2.5 pt-2 border-t border-border/50">
            {/* Primary display: loginUsername preferred over email */}
            {inv.loginUsername && (
              <div className="flex items-center gap-2.5 text-sm">
                <User className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                <span className="text-muted-foreground">账号：</span>
                <span className="text-foreground font-mono font-medium">{inv.loginUsername}</span>
              </div>
            )}
            {showEmail && (
              <div className="flex items-center gap-2.5 text-sm">
                <User className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                <span className="text-muted-foreground">邮箱：</span>
                <span className="text-foreground font-mono font-medium">{inv.targetEmail}</span>
              </div>
            )}
            <div className="flex items-center gap-2.5 text-sm">
              <Briefcase className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <span className="text-muted-foreground">工作区：</span>
              <span className="text-foreground font-medium">{inv.workspaceName}</span>
            </div>
            <div className="flex items-center gap-2.5 text-sm">
              <ShieldCheck className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <span className="text-muted-foreground">角色：</span>
              <span className="text-foreground">{roleLabel(inv.role)}</span>
            </div>
            <div className="flex items-center gap-2.5 text-sm">
              <Calendar className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <span className="text-muted-foreground">有效期：</span>
              <span className="text-foreground flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatExpiry(inv.expiresAt)}
              </span>
            </div>
          </div>
        </div>

        {/* loginUsername hint */}
        {inv.loginUsername && (
          <div className="rounded-lg border border-primary/20 bg-primary/10 px-4 py-3">
            <p className="text-primary/80 text-xs leading-relaxed">
              <span className="font-medium text-primary">提示：</span>
              管理员已为您分配用户名{' '}
              <span className="font-mono font-semibold">{inv.loginUsername}</span>，
              请使用此用户名完成接入。
            </p>
          </div>
        )}

        {/* Error alert */}
        {formErrors.general && (
          <Alert variant="destructive" className="border-destructive/50 bg-destructive/10">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{formErrors.general}</AlertDescription>
          </Alert>
        )}

        {/* Password policy hints */}
        {policyHints.length > 0 && (
          <div className="rounded-lg border border-border/50 bg-muted/30 px-4 py-3">
            <p className="text-muted-foreground text-xs font-medium mb-1.5">密码要求：</p>
            <ul className="space-y-0.5">
              {policyHints.map(hint => (
                <li key={hint} className="text-muted-foreground/70 text-xs flex items-center gap-1.5">
                  <span className="w-1 h-1 rounded-full bg-muted-foreground/50 flex-shrink-0" />
                  {hint}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Accept form */}
        <form onSubmit={handleAccept} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="inv-username" className="text-sm font-medium text-foreground">
              用户名
            </Label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
              <Input
                id="inv-username"
                type="text"
                autoComplete="username"
                placeholder="请输入用户名"
                value={username}
                onChange={e => {
                  setUsername(e.target.value);
                  if (formErrors.username) setFormErrors(prev => ({ ...prev, username: undefined }));
                }}
                className={`pl-10 bg-background/50 border-border/60 focus:border-primary/60 transition-colors ${
                  formErrors.username ? 'border-destructive' : ''
                }`}
                disabled={isBusy}
              />
            </div>
            {formErrors.username ? (
              <p className="text-destructive text-xs">{formErrors.username}</p>
            ) : inv.loginUsername ? (
              <p className="text-muted-foreground/60 text-xs">
                请使用管理员提供的用户名：<span className="font-mono">{inv.loginUsername}</span>
              </p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="inv-password" className="text-sm font-medium text-foreground">
              设置密码
            </Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
              <Input
                id="inv-password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="请设置您的登录密码"
                value={password}
                onChange={e => {
                  setPassword(e.target.value);
                  if (formErrors.password) setFormErrors(prev => ({ ...prev, password: undefined }));
                }}
                className={`pl-10 pr-10 bg-background/50 border-border/60 focus:border-primary/60 transition-colors ${
                  formErrors.password ? 'border-destructive' : ''
                }`}
                disabled={isBusy}
              />
              <button
                type="button"
                onClick={() => setShowPassword(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {formErrors.password && (
              <p className="text-destructive text-xs">{formErrors.password}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="inv-passwordConfirm" className="text-sm font-medium text-foreground">
              确认密码
            </Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
              <Input
                id="inv-passwordConfirm"
                type={showConfirm ? 'text' : 'password'}
                autoComplete="new-password"
                placeholder="请再次输入密码"
                value={passwordConfirm}
                onChange={e => {
                  setPasswordConfirm(e.target.value);
                  if (formErrors.passwordConfirm) setFormErrors(prev => ({ ...prev, passwordConfirm: undefined }));
                }}
                className={`pl-10 pr-10 bg-background/50 border-border/60 focus:border-primary/60 transition-colors ${
                  formErrors.passwordConfirm ? 'border-destructive' : ''
                }`}
                disabled={isBusy}
              />
              <button
                type="button"
                onClick={() => setShowConfirm(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                tabIndex={-1}
              >
                {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {formErrors.passwordConfirm && (
              <p className="text-destructive text-xs">{formErrors.passwordConfirm}</p>
            )}
          </div>

          <Button
            type="submit"
            className="w-full font-semibold h-11"
            disabled={isBusy}
          >
            {isBusy ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                正在接入...
              </>
            ) : (
              '设置初始密码并继续'
            )}
          </Button>
        </form>

        <div className="text-center">
          <button
            type="button"
            onClick={() => navigate('/login')}
            className="text-muted-foreground hover:text-foreground text-xs transition-colors underline underline-offset-2"
          >
            已有账号？返回登录
          </button>
        </div>
      </div>
    </div>
  );
}
