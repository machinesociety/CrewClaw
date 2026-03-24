/**
 * System Error Pages
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Per 页面清单与冻结边界.md §4 and UI_状态模型.md §4.6
 * - /error/403 - Forbidden
 * - /error/disabled - User disabled
 * - /error/bootstrap - Bootstrap failed
 * - 404 Not Found
 */

import { Link } from 'wouter';
import { Button } from '@/components/ui/button';
import { PublicShell } from '@/components/layout/AppShell';
import {
  ShieldOff,
  UserX,
  AlertTriangle,
  FileQuestion,
  ArrowLeft,
  RefreshCw,
} from 'lucide-react';

// ============================================================
// Generic error layout
// ============================================================

interface ErrorLayoutProps {
  icon: React.ReactNode;
  code: string;
  title: string;
  description: string;
  actions?: React.ReactNode;
}

function ErrorLayout({ icon, code, title, description, actions }: ErrorLayoutProps) {
  return (
    <PublicShell>
      <div className="w-full max-w-md text-center">
        <div className="bg-card border border-border rounded-xl p-10">
          <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-5">
            {icon}
          </div>
          <span className="mono text-xs text-muted-foreground/50 block mb-2">{code}</span>
          <h1
            className="text-2xl font-bold text-foreground mb-3"
            style={{ fontFamily: 'Space Grotesk' }}
          >
            {title}
          </h1>
          <p className="text-sm text-muted-foreground mb-6 leading-relaxed">{description}</p>
          {actions && (
            <div className="flex gap-2 justify-center">{actions}</div>
          )}
        </div>
      </div>
    </PublicShell>
  );
}

// ============================================================
// 403 Forbidden
// ============================================================

export function ForbiddenPage() {
  return (
    <ErrorLayout
      icon={<ShieldOff className="w-8 h-8 text-red-400" />}
      code="HTTP_403"
      title="无访问权限"
      description="您没有访问此页面的权限。如需访问，请联系管理员。"
      actions={
        <Link href="/app">
          <Button variant="outline" size="sm" className="gap-2">
            <ArrowLeft className="w-3.5 h-3.5" />
            返回工作台
          </Button>
        </Link>
      }
    />
  );
}

// ============================================================
// User Disabled
// ============================================================

export function UserDisabledPage() {
  return (
    <ErrorLayout
      icon={<UserX className="w-8 h-8 text-orange-400" />}
      code="USER_DISABLED"
      title="账号已禁用"
      description="您的账号已被管理员禁用，暂时无法访问平台。如有疑问，请联系管理员。"
      actions={
        <Link href="/login">
          <Button variant="outline" size="sm" className="gap-2">
            <ArrowLeft className="w-3.5 h-3.5" />
            返回登录
          </Button>
        </Link>
      }
    />
  );
}

// ============================================================
// Bootstrap Failed
// ============================================================

export function BootstrapFailedPage() {
  return (
    <ErrorLayout
      icon={<AlertTriangle className="w-8 h-8 text-yellow-400" />}
      code="BOOTSTRAP_FAILED"
      title="初始化失败"
      description="应用初始化时遇到了问题，无法加载会话信息。请刷新页面重试，如问题持续请联系管理员。"
      actions={
        <>
          <Button size="sm" className="gap-2" onClick={() => window.location.reload()}>
            <RefreshCw className="w-3.5 h-3.5" />
            刷新页面
          </Button>
          <Link href="/login">
            <Button variant="outline" size="sm" className="gap-2">
              <ArrowLeft className="w-3.5 h-3.5" />
              返回登录
            </Button>
          </Link>
        </>
      }
    />
  );
}

// ============================================================
// 404 Not Found
// ============================================================

export function NotFoundPage() {
  return (
    <ErrorLayout
      icon={<FileQuestion className="w-8 h-8 text-muted-foreground" />}
      code="HTTP_404"
      title="页面不存在"
      description="您访问的页面不存在或已被移除。"
      actions={
        <Link href="/app">
          <Button variant="outline" size="sm" className="gap-2">
            <ArrowLeft className="w-3.5 h-3.5" />
            返回工作台
          </Button>
        </Link>
      }
    />
  );
}
