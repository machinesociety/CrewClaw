/**
 * Login Page - /login
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Per 页面调用流程_BFF编排.md §4.1 and 页面清单与冻结边界.md §3.1
 * - Only shows local_password login method
 * - Reads /api/v1/auth/options
 * - Redirects to /app if already logged in
 */

import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { authApi, AuthOptionsResponse, isAppError } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Loader2, LogIn, Shield, Zap, Lock } from 'lucide-react';

type LoginPageState = 'loading' | 'ready' | 'redirecting' | 'error';

export default function LoginPage() {
  const [, navigate] = useLocation();
  const { bootState } = useAuth();
  const [pageState, setPageState] = useState<LoginPageState>('loading');
  const [options, setOptions] = useState<AuthOptionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // If already authenticated, redirect to app
  useEffect(() => {
    if (bootState === 'authenticatedReady') {
      navigate('/app');
    }
  }, [bootState, navigate]);

  // Load auth options
  useEffect(() => {
    async function loadOptions() {
      try {
        const opts = await authApi.options();
        setOptions(opts);
        setPageState('ready');
      } catch (e) {
        // If API not available, still show login button with default config
        setOptions({
          provider: 'authentik',
          methods: [{ type: 'local_password', enabled: true, label: '账号密码登录' }],
        });
        setPageState('ready');
      }
    }
    loadOptions();
  }, []);

  const handleLogin = () => {
    // Navigate to Authentik login flow
    // In production, this would redirect to the Authentik login URL
    setPageState('redirecting');
    // The actual redirect URL would come from the BFF
    window.location.href = '/api/v1/auth/login';
  };

  const localPasswordMethod = options?.methods?.find(
    (m) => m.type === 'local_password' && m.enabled
  );

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left panel - branding */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 relative overflow-hidden">
        {/* Background image */}
        <div className="absolute inset-0">
          <img
            src="https://d2xsxph8kpxj0f.cloudfront.net/310519663268444302/6zuH3qxGrch8vwpDVc4ZMU/clawloops-hero-bg-oDsU6vAAJLGfYqXm2WAN6e.webp"
            alt=""
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/70" />
        </div>

        <div className="relative">
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
              <span className="text-primary font-bold text-base" style={{ fontFamily: 'Space Grotesk' }}>CL</span>
            </div>
            <span className="text-xl font-semibold text-foreground" style={{ fontFamily: 'Space Grotesk' }}>
              ClawLoops
            </span>
          </div>

          <h1 className="text-3xl font-bold text-foreground mb-4 leading-tight" style={{ fontFamily: 'Space Grotesk' }}>
            AI 工作区<br />管理平台
          </h1>
          <p className="text-muted-foreground text-base leading-relaxed">
            为团队提供安全、可控的 AI 编程助手工作区，统一管理 runtime 生命周期与访问权限。
          </p>
        </div>

        <div className="relative space-y-4">
          {[
            { icon: Shield, title: '企业级安全', desc: '基于 Authentik 的统一身份认证' },
            { icon: Zap, title: '弹性 Runtime', desc: '按需启停，资源高效利用' },
            { icon: Lock, title: '精细权限控制', desc: '邀请制接入，workspace 级隔离' },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Icon className="w-4 h-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">{title}</p>
                <p className="text-xs text-muted-foreground">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel - login form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2.5 mb-8">
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
              <span className="text-primary font-bold text-sm" style={{ fontFamily: 'Space Grotesk' }}>CL</span>
            </div>
            <span className="font-semibold text-foreground" style={{ fontFamily: 'Space Grotesk' }}>
              ClawLoops
            </span>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
              欢迎回来
            </h2>
            <p className="text-muted-foreground text-sm">
              使用您的账号密码登录平台
            </p>
          </div>

          {pageState === 'loading' && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">加载中...</span>
            </div>
          )}

          {pageState === 'error' && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-4">
              <p className="text-sm text-red-400">{error}</p>
              <button
                className="text-xs text-red-400/70 mt-2 hover:text-red-400 underline"
                onClick={() => window.location.reload()}
              >
                重新加载
              </button>
            </div>
          )}

          {(pageState === 'ready' || pageState === 'redirecting') && (
            <div className="space-y-4">
              {localPasswordMethod ? (
                <Button
                  className="w-full gap-2 h-11"
                  onClick={handleLogin}
                  disabled={pageState === 'redirecting'}
                >
                  {pageState === 'redirecting' ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      正在跳转...
                    </>
                  ) : (
                    <>
                      <LogIn className="w-4 h-4" />
                      {localPasswordMethod.label || '账号密码登录'}
                    </>
                  )}
                </Button>
              ) : (
                <div className="rounded-lg bg-yellow-500/10 border border-yellow-500/20 p-4">
                  <p className="text-sm text-yellow-400">当前没有可用的登录方式</p>
                </div>
              )}

              <p className="text-xs text-muted-foreground text-center">
                首次使用？请联系管理员获取邀请链接
              </p>
            </div>
          )}

          {/* Provider info */}
          {options && (
            <div className="mt-8 pt-6 border-t border-border">
              <p className="text-xs text-muted-foreground/50 text-center">
                身份认证由 <span className="mono">{options.provider}</span> 提供
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
