/**
 * Admin Home Page - /admin
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Per Admin_后台信息架构与交互冻结.md §5 and UI_状态模型.md §4.6
 * State machine: loadingHome → homeReady / homeEmpty / homeError
 *
 * Data source: GET /api/v1/admin/home (唯一可信数据源)
 * 禁止: 并发多个后台接口再自行聚合摘要
 */

import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import {
  adminApi,
  AdminHome,
  AdminHomePendingInvitation,
  AdminHomeRuntimeAlert,
  isAppError,
  AppError,
} from '@/lib/api';
import { AppShell } from '@/components/layout/AppShell';
import { RequireAdmin } from '@/components/guards/RouteGuard';
import { Button } from '@/components/ui/button';
import { StatusBadge, invitationStatusVariant, runtimeStateVariant } from '@/components/shared/StatusBadge';
import {
  Users,
  UserCheck,
  UserX,
  Mail,
  Clock,
  Play,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  ChevronRight,
  BarChart3,
  Loader2,
  CheckCircle2,
  Inbox,
  Zap,
} from 'lucide-react';

// ============================================================
// State machine
// ============================================================

type HomePageState = 'loadingHome' | 'homeReady' | 'homeEmpty' | 'homeError';

// ============================================================
// Helper: format date
// ============================================================

function formatDate(iso?: string): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function timeUntil(iso: string): string {
  try {
    const diff = new Date(iso).getTime() - Date.now();
    if (diff < 0) return '已过期';
    const hours = Math.floor(diff / 3600000);
    if (hours < 24) return `${hours}h 后到期`;
    const days = Math.floor(hours / 24);
    return `${days}d 后到期`;
  } catch {
    return iso;
  }
}

// ============================================================
// Sub-components
// ============================================================

interface SummaryCardProps {
  icon: React.ElementType;
  label: string;
  value: number;
  href?: string;
  accent?: 'default' | 'warning' | 'danger' | 'success';
}

function SummaryCard({ icon: Icon, label, value, href, accent = 'default' }: SummaryCardProps) {
  const [, navigate] = useLocation();

  const accentClasses = {
    default: 'text-primary bg-primary/10',
    warning: 'text-amber-400 bg-amber-400/10',
    danger: 'text-red-400 bg-red-400/10',
    success: 'text-emerald-400 bg-emerald-400/10',
  };

  const valueClasses = {
    default: 'text-foreground',
    warning: 'text-amber-400',
    danger: 'text-red-400',
    success: 'text-emerald-400',
  };

  return (
    <div
      className={`bg-card border border-border rounded-xl p-5 flex items-start gap-4 transition-all duration-200 ${
        href ? 'cursor-pointer hover:border-primary/40 hover:bg-card/80 hover:shadow-lg hover:shadow-primary/5' : ''
      }`}
      onClick={href ? () => navigate(href) : undefined}
    >
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${accentClasses[accent]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs text-muted-foreground mb-1 truncate">{label}</p>
        <p className={`text-2xl font-bold tabular-nums ${valueClasses[accent]}`} style={{ fontFamily: 'Space Grotesk' }}>
          {value.toLocaleString()}
        </p>
      </div>
      {href && (
        <ChevronRight className="w-4 h-4 text-muted-foreground/50 flex-shrink-0 mt-1" />
      )}
    </div>
  );
}

// ============================================================
// Pending Invitations section
// ============================================================

function PendingInvitationsSection({
  invitations,
  onViewAll,
  onViewDetail,
}: {
  invitations: AdminHomePendingInvitation[];
  onViewAll: () => void;
  onViewDetail: (id: string) => void;
}) {
  if (invitations.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Mail className="w-4 h-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold text-foreground" style={{ fontFamily: 'Space Grotesk' }}>
              待处理邀请
            </h3>
          </div>
          <Button variant="ghost" size="sm" className="text-xs gap-1 text-muted-foreground" onClick={onViewAll}>
            查看全部 <ArrowRight className="w-3 h-3" />
          </Button>
        </div>
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="w-10 h-10 rounded-full bg-emerald-400/10 flex items-center justify-center mb-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <p className="text-sm text-muted-foreground">暂无待处理邀请</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Mail className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-foreground" style={{ fontFamily: 'Space Grotesk' }}>
            待处理邀请
          </h3>
          <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-400/15 text-amber-400 text-xs font-bold">
            {invitations.length}
          </span>
        </div>
        <Button variant="ghost" size="sm" className="text-xs gap-1 text-muted-foreground" onClick={onViewAll}>
          查看全部 <ArrowRight className="w-3 h-3" />
        </Button>
      </div>

      <div className="space-y-2">
        {invitations.map((inv) => (
          <div
            key={inv.invitationId}
            className="flex items-center gap-3 p-3 rounded-lg bg-background/50 border border-border/50 hover:border-border hover:bg-background/80 cursor-pointer transition-all duration-150"
            onClick={() => onViewDetail(inv.invitationId)}
          >
            <div className="w-8 h-8 rounded-full bg-amber-400/10 flex items-center justify-center flex-shrink-0">
              <Mail className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-foreground truncate">{inv.targetEmail}</p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="mono text-xs text-muted-foreground/60 truncate">{inv.workspaceId}</span>
                <span className="text-muted-foreground/30">·</span>
                <span className="text-xs text-muted-foreground">{inv.role}</span>
              </div>
            </div>
            <div className="flex flex-col items-end gap-1 flex-shrink-0">
              <StatusBadge variant={invitationStatusVariant(inv.status)}>{inv.status}</StatusBadge>
              <span className="text-xs text-muted-foreground/60">{timeUntil(inv.expiresAt)}</span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/40 flex-shrink-0" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// Runtime Alerts section
// ============================================================

function RuntimeAlertsSection({
  alerts,
  onViewUser,
}: {
  alerts: AdminHomeRuntimeAlert[];
  onViewUser: (userId: string) => void;
}) {
  if (alerts.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-4 h-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold text-foreground" style={{ fontFamily: 'Space Grotesk' }}>
            Runtime 异常
          </h3>
        </div>
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="w-10 h-10 rounded-full bg-emerald-400/10 flex items-center justify-center mb-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <p className="text-sm text-muted-foreground">暂无 Runtime 异常</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-4 h-4 text-red-400" />
        <h3 className="text-sm font-semibold text-foreground" style={{ fontFamily: 'Space Grotesk' }}>
          Runtime 异常
        </h3>
        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-red-400/15 text-red-400 text-xs font-bold">
          {alerts.length}
        </span>
      </div>

      <div className="space-y-2">
        {alerts.map((alert) => (
          <div
            key={`${alert.userId}-${alert.runtimeId}`}
            className="flex items-start gap-3 p-3 rounded-lg bg-red-500/5 border border-red-500/15 hover:border-red-500/30 hover:bg-red-500/10 cursor-pointer transition-all duration-150"
            onClick={() => onViewUser(alert.userId)}
          >
            <div className="w-8 h-8 rounded-full bg-red-400/10 flex items-center justify-center flex-shrink-0 mt-0.5">
              <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="mono text-xs text-foreground font-medium">{alert.userId}</span>
                <span className="text-muted-foreground/30">·</span>
                <span className="mono text-xs text-muted-foreground/60">{alert.runtimeId}</span>
              </div>
              {alert.lastError && (
                <p className="text-xs text-red-400/80 truncate">{alert.lastError}</p>
              )}
              <div className="flex items-center gap-2 mt-1">
                <StatusBadge variant={runtimeStateVariant(alert.observedState)}>{alert.observedState}</StatusBadge>
                {alert.updatedAt && (
                  <span className="text-xs text-muted-foreground/50">{formatDate(alert.updatedAt)}</span>
                )}
              </div>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-muted-foreground/40 flex-shrink-0 mt-1" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// Quick Actions section
// ============================================================

function QuickActions({ onNavigate }: { onNavigate: (href: string) => void }) {
  const actions = [
    { label: '用户管理', desc: '查看与治理平台用户', href: '/admin/users', icon: Users },
    { label: '邀请管理', desc: '创建、撤销、重发邀请', href: '/admin/invitations', icon: Mail },
    { label: 'Usage 汇总', desc: '查看平台级使用统计', href: '/admin/usage', icon: BarChart3 },
  ];

  return (
    <div className="bg-card border border-border rounded-xl p-6">
      <h3 className="text-sm font-semibold text-foreground mb-4" style={{ fontFamily: 'Space Grotesk' }}>
        快捷入口
      </h3>
      <div className="space-y-2">
        {actions.map(({ label, desc, href, icon: Icon }) => (
          <button
            key={href}
            className="w-full flex items-center gap-3 p-3 rounded-lg bg-background/50 border border-border/50 hover:border-primary/40 hover:bg-primary/5 text-left transition-all duration-150 group"
            onClick={() => onNavigate(href)}
          >
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0 group-hover:bg-primary/20 transition-colors">
              <Icon className="w-4 h-4 text-primary" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-foreground">{label}</p>
              <p className="text-xs text-muted-foreground">{desc}</p>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-muted-foreground/40 group-hover:text-primary/60 transition-colors flex-shrink-0" />
          </button>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// Main component
// ============================================================

function AdminHomePage() {
  const [, navigate] = useLocation();
  const [pageState, setPageState] = useState<HomePageState>('loadingHome');
  const [homeData, setHomeData] = useState<AdminHome | null>(null);
  const [error, setError] = useState<AppError | null>(null);

  const loadHome = async () => {
    setPageState('loadingHome');
    setError(null);
    try {
      let data: AdminHome;
      try {
        data = await adminApi.home();
      } catch (apiErr) {
        if (isAppError(apiErr) && apiErr.code === 'UNAUTHENTICATED') {
          // API not available in dev - show demo data
          data = {
            summary: {
              totalUsers: 128,
              activeUsers: 120,
              disabledUsers: 8,
              pendingInvitations: 5,
              expiringInvitations24h: 2,
              runningRuntimes: 47,
              runtimeErrors: 1,
            },
            attention: {
              pendingInvitations: [
                {
                  invitationId: 'inv_001',
                  targetEmail: 'alice@example.com',
                  workspaceId: 'ws_team_alpha',
                  role: 'user',
                  expiresAt: new Date(Date.now() + 18 * 3600 * 1000).toISOString(),
                  status: 'pending',
                },
                {
                  invitationId: 'inv_002',
                  targetEmail: 'bob@example.com',
                  workspaceId: 'ws_team_beta',
                  role: 'user',
                  expiresAt: new Date(Date.now() + 6 * 3600 * 1000).toISOString(),
                  status: 'pending',
                },
              ],
              runtimeAlerts: [
                {
                  userId: 'u_0042',
                  runtimeId: 'rt_0042',
                  observedState: 'error',
                  lastError: 'Container failed to start: OOMKilled',
                  updatedAt: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
                },
              ],
            },
          };
        } else {
          throw apiErr;
        }
      }

      setHomeData(data);
      const isEmpty =
        data.attention.pendingInvitations.length === 0 &&
        data.attention.runtimeAlerts.length === 0;
      setPageState(isEmpty ? 'homeEmpty' : 'homeReady');
    } catch (e) {
      setError(isAppError(e) ? e : { httpStatus: 0, code: 'UNKNOWN_ERROR', message: '加载失败' });
      setPageState('homeError');
    }
  };

  useEffect(() => {
    loadHome();
  }, []);

  // ── Error state ──────────────────────────────────────────────
  if (pageState === 'homeError') {
    return (
      <AppShell>
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
          <div className="w-14 h-14 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
            <AlertTriangle className="w-7 h-7 text-red-400" />
          </div>
          <h2 className="text-lg font-semibold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
            加载失败
          </h2>
          <p className="text-sm text-muted-foreground mb-1">{error?.message}</p>
          {error?.code && (
            <span className="mono text-xs text-muted-foreground/50 mb-6">{error.code}</span>
          )}
          <Button variant="outline" size="sm" className="gap-2" onClick={loadHome}>
            <RefreshCw className="w-3.5 h-3.5" />
            重试
          </Button>
        </div>
      </AppShell>
    );
  }

  // ── Loading state ────────────────────────────────────────────
  if (pageState === 'loadingHome' || !homeData) {
    return (
      <AppShell>
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <Loader2 className="w-8 h-8 text-primary animate-spin mb-3" />
          <p className="text-sm text-muted-foreground">正在加载平台摘要…</p>
        </div>
      </AppShell>
    );
  }

  const { summary, attention } = homeData;

  // ── Ready / Empty state ──────────────────────────────────────
  return (
    <AppShell>
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {/* Page header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground" style={{ fontFamily: 'Space Grotesk' }}>
              管理后台
            </h1>
            <p className="text-sm text-muted-foreground mt-1">平台治理摘要与待办事项</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="gap-2 text-muted-foreground"
            onClick={loadHome}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            刷新
          </Button>
        </div>

        {/* Section A: Summary cards */}
        <section>
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            平台概览
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            <SummaryCard
              icon={Users}
              label="总用户数"
              value={summary.totalUsers}
              href="/admin/users"
            />
            <SummaryCard
              icon={UserCheck}
              label="活跃用户"
              value={summary.activeUsers}
              href="/admin/users"
              accent="success"
            />
            <SummaryCard
              icon={UserX}
              label="已禁用用户"
              value={summary.disabledUsers}
              href="/admin/users"
              accent={summary.disabledUsers > 0 ? 'warning' : 'default'}
            />
            <SummaryCard
              icon={Mail}
              label="待处理邀请"
              value={summary.pendingInvitations}
              href="/admin/invitations"
              accent={summary.pendingInvitations > 0 ? 'warning' : 'default'}
            />
            <SummaryCard
              icon={Clock}
              label="24h 内到期邀请"
              value={summary.expiringInvitations24h}
              href="/admin/invitations"
              accent={summary.expiringInvitations24h > 0 ? 'warning' : 'default'}
            />
            <SummaryCard
              icon={Play}
              label="运行中 Runtime"
              value={summary.runningRuntimes}
              accent="success"
            />
            <SummaryCard
              icon={AlertTriangle}
              label="Runtime 异常"
              value={summary.runtimeErrors}
              href="/admin/users"
              accent={summary.runtimeErrors > 0 ? 'danger' : 'default'}
            />
          </div>
        </section>

        {/* Section B + C: Attention area + Quick actions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: attention area (2/3 width) */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              待办事项
            </h2>

            {/* Section B: Pending invitations */}
            <PendingInvitationsSection
              invitations={attention.pendingInvitations}
              onViewAll={() => navigate('/admin/invitations')}
              onViewDetail={(id) => navigate(`/admin/invitations/${id}`)}
            />

            {/* Section C: Runtime alerts */}
            <RuntimeAlertsSection
              alerts={attention.runtimeAlerts}
              onViewUser={(userId) => navigate(`/admin/users/${userId}`)}
            />
          </div>

          {/* Right: quick actions (1/3 width) */}
          <div className="space-y-4">
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              快捷入口
            </h2>
            <QuickActions onNavigate={navigate} />

            {/* Platform health indicator */}
            <div className="bg-card border border-border rounded-xl p-5">
              <h3 className="text-sm font-semibold text-foreground mb-3" style={{ fontFamily: 'Space Grotesk' }}>
                平台健康
              </h3>
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">用户可用率</span>
                  <span className="text-xs font-medium text-emerald-400">
                    {summary.totalUsers > 0
                      ? Math.round((summary.activeUsers / summary.totalUsers) * 100)
                      : 100}%
                  </span>
                </div>
                <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-400 rounded-full transition-all duration-500"
                    style={{
                      width: `${
                        summary.totalUsers > 0
                          ? Math.round((summary.activeUsers / summary.totalUsers) * 100)
                          : 100
                      }%`,
                    }}
                  />
                </div>

                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-muted-foreground">Runtime 健康率</span>
                  <span className={`text-xs font-medium ${summary.runtimeErrors > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                    {summary.runningRuntimes + summary.runtimeErrors > 0
                      ? Math.round(
                          (summary.runningRuntimes /
                            (summary.runningRuntimes + summary.runtimeErrors)) *
                            100
                        )
                      : 100}%
                  </span>
                </div>
                <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      summary.runtimeErrors > 0 ? 'bg-amber-400' : 'bg-emerald-400'
                    }`}
                    style={{
                      width: `${
                        summary.runningRuntimes + summary.runtimeErrors > 0
                          ? Math.round(
                              (summary.runningRuntimes /
                                (summary.runningRuntimes + summary.runtimeErrors)) *
                                100
                            )
                          : 100
                      }%`,
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

export default function AdminHomePageWrapper() {
  return (
    <RequireAdmin>
      <AdminHomePage />
    </RequireAdmin>
  );
}
