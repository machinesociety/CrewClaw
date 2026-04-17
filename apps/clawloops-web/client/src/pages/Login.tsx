import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { authApi, AuthOptionsResponse, isAppError, getErrorCode } from '@/lib/api';
import { RedirectIfAuthenticated } from '@/components/guards/RouteGuard';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Eye, EyeOff, Loader2, AlertCircle, Lock, User, Shield, Zap } from 'lucide-react';
import AnimatedLoginArt from '@/components/auth/AnimatedLoginArt';

type LoginState = 'idle' | 'submitting' | 'success';

interface FormErrors {
  username?: string;
  password?: string;
  general?: string;
}

function LoginForm() {
  const [, navigate] = useLocation();
  const { refresh } = useAuth();
  const [options, setOptions] = useState<AuthOptionsResponse | null>(null);
  const [loginState, setLoginState] = useState<LoginState>('idle');
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [activeField, setActiveField] = useState<'username' | 'password' | null>(null);
  const [pointer, setPointer] = useState({ x: 0.5, y: 0.5 });

  useEffect(() => {
    authApi.options().then(setOptions).catch(() => {
      setOptions({
        provider: 'local',
        methods: [{ type: 'local_password', label: '用户名优先登录' }],
      });
    });
  }, []);

  const validate = (): boolean => {
    const errors: FormErrors = {};
    if (!username.trim()) errors.username = '请输入用户名';
    if (!password) errors.password = '请输入密码';
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoginState('submitting');
    setFormErrors({});

    try {
      const result = await authApi.login({ username: username.trim(), password });
      setLoginState('success');

      try {
        await refresh();
      } catch {
        // ignore
      }

      if (result.redirectTo === '/force-password-change' || result.mustChangePassword) {
        navigate('/force-password-change');
      } else if (result.redirectTo === '/admin') {
        navigate('/admin');
      } else if (result.redirectTo === '/app') {
        navigate('/app');
      } else {
        const isAdmin = result.user?.isAdmin ?? result.user?.role === 'admin';
        navigate(isAdmin ? '/admin' : '/app');
      }
    } catch (e) {
      setLoginState('idle');
      const code = getErrorCode(e);

      if (code === 'INVALID_CREDENTIALS') {
        setFormErrors({ general: '用户名或密码错误，请重新输入' });
      } else if (code === 'USER_DISABLED') {
        setFormErrors({ general: '账号已被禁用，请联系管理员' });
      } else if (code === 'PASSWORD_CHANGE_REQUIRED') {
        navigate('/force-password-change');
      } else if (code === 'SESSION_ERROR') {
        setFormErrors({ general: '系统繁忙，请稍后重试' });
      } else if (isAppError(e) && e.httpStatus === 401) {
        setFormErrors({ general: '用户名或密码错误，请重新输入' });
      } else {
        setFormErrors({ general: '登录失败，请稍后重试' });
      }
    }
  };

  const localMethod = options?.methods?.find((m) => m.type === 'local_password');
  const buttonLabel = localMethod?.label ?? '用户名优先登录';
  const isBusy = loginState === 'submitting' || loginState === 'success';
  const artMode: 'idle' | 'email' | 'password' | 'password-visible' | 'error' = formErrors.general
    ? 'error'
    : activeField === 'username'
      ? 'email'
      : activeField === 'password'
        ? (showPassword ? 'password-visible' : 'password')
        : 'idle';

  return (
    <div className="min-h-screen bg-background flex">
      <div
        className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 overflow-hidden border-r border-black/5"
        onMouseMove={(e) => {
          const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
          setPointer({
            x: (e.clientX - rect.left) / Math.max(rect.width, 1),
            y: (e.clientY - rect.top) / Math.max(rect.height, 1),
          });
        }}
        style={{ background: 'linear-gradient(160deg, #efecf6 0%, #ece9f4 48%, #e7e4f0 100%)' }}
      >
        <div className="absolute inset-0 opacity-25 bg-[radial-gradient(circle_at_10%_10%,rgba(255,255,255,0.8),transparent_40%),radial-gradient(circle_at_90%_20%,rgba(255,255,255,0.5),transparent_35%)]" />

        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/15 border border-primary/25 flex items-center justify-center backdrop-blur-sm">
              <span className="text-primary font-bold text-base" style={{ fontFamily: 'Space Grotesk' }}>CL</span>
            </div>
            <span className="text-foreground font-bold text-xl" style={{ fontFamily: 'Space Grotesk' }}>ClawLoops</span>
          </div>
        </div>

        <div className="relative z-10 grid grid-cols-[360px_1fr] gap-8 items-center flex-1">
          <div className="max-w-[360px]">
            <h1 className="text-[64px] font-bold text-foreground leading-[1.05] tracking-tight" style={{ fontFamily: 'Space Grotesk' }}>
              AI 工作区
              <br />
              <span className="text-primary">管理平台</span>
            </h1>
            <p className="mt-6 text-foreground/70 text-lg leading-relaxed font-medium" style={{ fontFamily: 'Space Grotesk' }}>
              统一管理用户、模型与 Runtime，
              <br />
              为团队提供安全可控的 AI 工作环境。
            </p>
            <div className="mt-10 space-y-5">
              {[
                { icon: Shield, title: '企业级安全', desc: '邀请制接入，会话级容器隔离' },
                { icon: Zap, title: '弹性 Runtime', desc: '按需启停，毫秒级资源分配' },
                { icon: Lock, title: '精细权限控制', desc: 'Workspace 级模型与数据访问策略' },
              ].map(({ icon: Icon, title, desc }) => (
                <div key={title} className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/15 border border-primary/25 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
                    <Icon className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-base font-bold text-foreground">{title}</p>
                    <p className="text-sm text-foreground/50">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="h-full flex items-end justify-center relative pb-12">
            <div className="absolute bottom-[72px] left-1/2 -translate-x-1/2 w-[380px] h-[40px] bg-primary/10 blur-[40px] rounded-[100%] pointer-events-none" />
            <AnimatedLoginArt mode={artMode} pointer={pointer} />
          </div>
        </div>

        <div className="relative z-10">
          <p className="text-foreground/40 text-xs">ClawLoops Platform · 内部使用</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-9 h-9 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center">
              <span className="text-primary font-bold text-sm" style={{ fontFamily: 'Space Grotesk' }}>CL</span>
            </div>
            <span className="text-foreground font-bold text-lg" style={{ fontFamily: 'Space Grotesk' }}>ClawLoops</span>
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-foreground" style={{ fontFamily: 'Space Grotesk' }}>
              欢迎回来
            </h2>
            <p className="text-muted-foreground text-sm">请使用管理员提供的账号登录</p>
          </div>

          <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3">
            <p className="text-amber-500 text-xs leading-relaxed">
              <span className="font-medium">提示：</span>
              请优先使用管理员提供的用户名登录。如未收到账号信息，请联系您的管理员。
            </p>
          </div>

          {formErrors.general && (
            <Alert variant="destructive" className="border-destructive/50 bg-destructive/10">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{formErrors.general}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-sm font-medium text-foreground">用户名</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                <Input
                  id="username"
                  type="text"
                  autoComplete="username"
                  placeholder="请输入用户名"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    if (formErrors.username) setFormErrors((prev) => ({ ...prev, username: undefined }));
                    if (formErrors.general) setFormErrors((prev) => ({ ...prev, general: undefined }));
                  }}
                  onFocus={() => setActiveField('username')}
                  onBlur={() => setActiveField(null)}
                  onMouseMove={(e) => {
                    const rect = (e.currentTarget as HTMLInputElement).getBoundingClientRect();
                    setPointer({
                      x: (e.clientX - rect.left) / Math.max(rect.width, 1),
                      y: (e.clientY - rect.top) / Math.max(rect.height, 1),
                    });
                  }}
                  className={`pl-10 bg-background/50 border-border/60 focus:border-primary/60 transition-colors ${
                    formErrors.username ? 'border-destructive' : ''
                  }`}
                  disabled={isBusy}
                />
              </div>
              {formErrors.username && <p className="text-destructive text-xs">{formErrors.username}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium text-foreground">密码</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="请输入密码"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (formErrors.password) setFormErrors((prev) => ({ ...prev, password: undefined }));
                    if (formErrors.general) setFormErrors((prev) => ({ ...prev, general: undefined }));
                  }}
                  onFocus={() => setActiveField('password')}
                  onBlur={() => setActiveField(null)}
                  onMouseMove={(e) => {
                    const rect = (e.currentTarget as HTMLInputElement).getBoundingClientRect();
                    setPointer({
                      x: (e.clientX - rect.left) / Math.max(rect.width, 1),
                      y: (e.clientY - rect.top) / Math.max(rect.height, 1),
                    });
                  }}
                  className={`pl-10 pr-10 bg-background/50 border-border/60 focus:border-primary/60 transition-colors ${
                    formErrors.password ? 'border-destructive' : ''
                  }`}
                  disabled={isBusy}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {formErrors.password && <p className="text-destructive text-xs">{formErrors.password}</p>}
            </div>

            <Button type="submit" className="w-full font-semibold h-11" disabled={isBusy}>
              {loginState === 'submitting' ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  登录中...
                </>
              ) : loginState === 'success' ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  跳转中...
                </>
              ) : (
                buttonLabel
              )}
            </Button>
          </form>

          <p className="text-center text-muted-foreground/50 text-xs">首次使用？请联系系统管理员获取邀请链接</p>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <RedirectIfAuthenticated>
      <LoginForm />
    </RedirectIfAuthenticated>
  );
}
