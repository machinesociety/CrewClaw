/**
 * Admin Users Pages - /admin/users and /admin/users/:userId
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Per 页面调用流程_BFF编排.md §6.1, §6.2
 * List: userId, subjectId, role, status, authMethod, runtimeObservedState, lastLoginAt
 * Actions: enable/disable, view detail
 */

import { useCallback, useEffect, useState } from 'react';
import { useParams, Link } from 'wouter';
import {
  adminApi,
  AdminUser,
  AdminUserDetail,
  RuntimeBinding,
  isAppError,
} from '@/lib/api';
import { RequireAdmin } from '@/components/guards/RouteGuard';
import { AppShell } from '@/components/layout/AppShell';
import {
  StatusBadge,
  userStatusVariant,
  runtimeStateVariant,
} from '@/components/shared/StatusBadge';
import {
  PageHeader,
  LoadingRows,
  ErrorDisplay,
  EmptyState,
  MonoText,
  InfoRow,
  ConfirmDialog,
} from '@/components/shared/PageComponents';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import {
  RefreshCw,
  ChevronRight,
  UserX,
  UserCheck,
  ArrowLeft,
  Loader2,
  Users,
  Cpu,
} from 'lucide-react';

// ============================================================
// Users List Page
// ============================================================

function UsersListContent() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [patchingUserId, setPatchingUserId] = useState<string | null>(null);
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    userId: string;
    action: 'enable' | 'disable';
  } | null>(null);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminApi.users.list();
      setUsers(res.users || []);
    } catch (e) {
      setError(isAppError(e) ? e.message : '加载用户列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleStatusChange = async (userId: string, newStatus: 'active' | 'disabled') => {
    setPatchingUserId(userId);
    try {
      await adminApi.users.updateStatus(userId, newStatus);
      toast.success(`用户已${newStatus === 'active' ? '启用' : '禁用'}`);
      await loadUsers();
    } catch (e) {
      toast.error(isAppError(e) ? e.message : '操作失败');
    } finally {
      setPatchingUserId(null);
      setConfirmDialog(null);
    }
  };

  function formatDate(iso?: string) {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short', timeZone: 'Asia/Shanghai' });
    } catch {
      return iso;
    }
  }

  return (
    <div className="page-enter">
      <PageHeader
        title="用户管理"
        description="管理平台用户账号状态"
        actions={
          <Button variant="outline" size="sm" className="gap-2" onClick={loadUsers} disabled={loading}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
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
            <ErrorDisplay message={error} onRetry={loadUsers} className="py-8" />
          )}

          {!loading && !error && users.length === 0 && (
            <EmptyState
              title="暂无用户"
              description="还没有注册用户"
              icon={<Users className="w-6 h-6 text-muted-foreground" />}
            />
          )}

          {!loading && !error && users.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>用户 ID</TableHead>
                  <TableHead>Subject ID</TableHead>
                  <TableHead>角色</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>认证方式</TableHead>
                  <TableHead>Runtime 状态</TableHead>
                  <TableHead>最近登录</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.userId}>
                    <TableCell>
                      <MonoText className="text-foreground">{user.userId}</MonoText>
                    </TableCell>
                    <TableCell>
                      <MonoText>{user.subjectId}</MonoText>
                    </TableCell>
                    <TableCell>
                      <StatusBadge variant={user.role === 'admin' ? 'info' : 'neutral'}>
                        {user.role}
                      </StatusBadge>
                    </TableCell>
                    <TableCell>
                      <StatusBadge variant={userStatusVariant(user.status)} dot={user.status === 'active'}>
                        {user.status === 'active' ? '启用' : '禁用'}
                      </StatusBadge>
                    </TableCell>
                    <TableCell>
                      <MonoText>{user.authMethod}</MonoText>
                    </TableCell>
                    <TableCell>
                      {user.runtimeObservedState ? (
                        <StatusBadge variant={runtimeStateVariant(user.runtimeObservedState)}>
                          {user.runtimeObservedState}
                        </StatusBadge>
                      ) : (
                        <span className="text-muted-foreground/40 text-xs">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="text-xs text-muted-foreground">{formatDate(user.lastLoginAt)}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs gap-1"
                          disabled={patchingUserId === user.userId}
                          onClick={() =>
                            setConfirmDialog({
                              open: true,
                              userId: user.userId,
                              action: user.status === 'active' ? 'disable' : 'enable',
                            })
                          }
                        >
                          {patchingUserId === user.userId ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : user.status === 'active' ? (
                            <UserX className="w-3 h-3 text-destructive" />
                          ) : (
                            <UserCheck className="w-3 h-3 text-green-400" />
                          )}
                          {user.status === 'active' ? '禁用' : '启用'}
                        </Button>
                        <Link href={`/admin/users/${user.userId}`}>
                          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1">
                            详情
                            <ChevronRight className="w-3 h-3" />
                          </Button>
                        </Link>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {confirmDialog && (
        <ConfirmDialog
          open={confirmDialog.open}
          onOpenChange={(open) => !open && setConfirmDialog(null)}
          title={confirmDialog.action === 'disable' ? '禁用用户' : '启用用户'}
          description={`确认要${confirmDialog.action === 'disable' ? '禁用' : '启用'}用户 ${confirmDialog.userId} 吗？`}
          confirmLabel={confirmDialog.action === 'disable' ? '禁用' : '启用'}
          destructive={confirmDialog.action === 'disable'}
          onConfirm={() =>
            handleStatusChange(
              confirmDialog.userId,
              confirmDialog.action === 'disable' ? 'disabled' : 'active'
            )
          }
        />
      )}
    </div>
  );
}

export function AdminUsersListPage() {
  return (
    <RequireAdmin>
      <AppShell>
        <UsersListContent />
      </AppShell>
    </RequireAdmin>
  );
}

// ============================================================
// User Detail Page
// ============================================================

function UserDetailContent() {
  const params = useParams<{ userId: string }>();
  const userId = params.userId;

  const [user, setUser] = useState<AdminUserDetail | null>(null);
  const [runtime, setRuntime] = useState<RuntimeBinding | null>(null);
  const [userLoading, setUserLoading] = useState(true);
  const [runtimeLoading, setRuntimeLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [patchingStatus, setPatchingStatus] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState(false);

  const loadUser = useCallback(async () => {
    if (!userId) return;
    setUserLoading(true);
    try {
      const data = await adminApi.users.get(userId);
      setUser(data);
    } catch (e) {
      setError(isAppError(e) ? e.message : '加载用户详情失败');
    } finally {
      setUserLoading(false);
    }
  }, [userId]);

  const loadRuntime = useCallback(async () => {
    if (!userId) return;
    setRuntimeLoading(true);
    try {
      const res = await adminApi.users.getRuntime(userId);
      setRuntime(res.runtime || null);
    } catch (e) {
      if (isAppError(e) && e.code === 'RUNTIME_NOT_FOUND') {
        setRuntime(null);
      }
      // Non-critical, ignore other errors
    } finally {
      setRuntimeLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadUser();
    loadRuntime();
  }, [loadUser, loadRuntime]);

  const handleStatusToggle = async () => {
    if (!user) return;
    const newStatus = user.status === 'active' ? 'disabled' : 'active';
    setPatchingStatus(true);
    try {
      await adminApi.users.updateStatus(userId!, newStatus);
      toast.success(`用户已${newStatus === 'active' ? '启用' : '禁用'}`);
      await loadUser();
      await loadRuntime();
    } catch (e) {
      toast.error(isAppError(e) ? e.message : '操作失败');
    } finally {
      setPatchingStatus(false);
      setConfirmDialog(false);
    }
  };

  function formatDate(iso?: string) {
    if (!iso) return undefined;
    try {
      return new Date(iso).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
    } catch {
      return iso;
    }
  }

  return (
    <div className="page-enter">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/admin/users">
          <Button variant="ghost" size="sm" className="gap-2 -ml-2">
            <ArrowLeft className="w-3.5 h-3.5" />
            用户列表
          </Button>
        </Link>
        <span className="text-muted-foreground/40">/</span>
        <span className="text-sm text-muted-foreground mono">{userId}</span>
      </div>

      {error && <ErrorDisplay message={error} onRetry={loadUser} />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* User info card */}
        <Card className="card-glow">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base" style={{ fontFamily: 'Space Grotesk' }}>
                用户信息
              </CardTitle>
              {user && (
                <Button
                  size="sm"
                  variant={user.status === 'active' ? 'destructive' : 'outline'}
                  className="gap-1.5 h-7 text-xs"
                  disabled={patchingStatus}
                  onClick={() => setConfirmDialog(true)}
                >
                  {patchingStatus ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : user.status === 'active' ? (
                    <UserX className="w-3 h-3" />
                  ) : (
                    <UserCheck className="w-3 h-3" />
                  )}
                  {user.status === 'active' ? '禁用账号' : '启用账号'}
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {userLoading && (
              <div className="space-y-2">
                {[1, 2, 3, 4].map((i) => <div key={i} className="h-8 skeleton rounded" />)}
              </div>
            )}
            {user && (
              <div className="space-y-0">
                <InfoRow label="用户 ID" value={<MonoText>{user.userId}</MonoText>} />
                <InfoRow label="Subject ID" value={<MonoText>{user.subjectId}</MonoText>} />
                <InfoRow label="租户 ID" value={<MonoText>{user.tenantId}</MonoText>} />
                <InfoRow label="角色" value={
                  <StatusBadge variant={user.role === 'admin' ? 'info' : 'neutral'}>{user.role}</StatusBadge>
                } />
                <InfoRow label="状态" value={
                  <StatusBadge variant={userStatusVariant(user.status)} dot={user.status === 'active'}>
                    {user.status === 'active' ? '启用' : '禁用'}
                  </StatusBadge>
                } />
                <InfoRow label="认证方式" value={<MonoText>{user.authMethod}</MonoText>} />
                <InfoRow label="最近登录" value={formatDate(user.lastLoginAt)} />
                <InfoRow label="创建时间" value={formatDate(user.createdAt)} />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Runtime card */}
        <Card className="card-glow">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2" style={{ fontFamily: 'Space Grotesk' }}>
              <Cpu className="w-4 h-4 text-primary" />
              Runtime 详情
            </CardTitle>
          </CardHeader>
          <CardContent>
            {runtimeLoading && (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => <div key={i} className="h-8 skeleton rounded" />)}
              </div>
            )}
            {!runtimeLoading && !runtime && (
              <p className="text-sm text-muted-foreground text-center py-4">暂无 Runtime</p>
            )}
            {runtime && (
              <div className="space-y-0">
                <InfoRow label="Runtime ID" value={<MonoText>{runtime.runtimeId}</MonoText>} />
                <InfoRow label="Volume ID" value={<MonoText>{runtime.volumeId}</MonoText>} />
                <InfoRow label="期望状态" value={
                  <StatusBadge variant={runtimeStateVariant(runtime.desiredState)}>{runtime.desiredState}</StatusBadge>
                } />
                <InfoRow label="观测状态" value={
                  <StatusBadge variant={runtimeStateVariant(runtime.observedState)}>{runtime.observedState}</StatusBadge>
                } />
                <InfoRow label="保留策略" value={<MonoText>{runtime.retentionPolicy}</MonoText>} />
                <InfoRow label="内部端点" value={<MonoText>{runtime.internalEndpoint}</MonoText>} />
                {runtime.browserUrl && (
                  <InfoRow label="Browser URL" value={<MonoText className="text-blue-400/70">{runtime.browserUrl}</MonoText>} />
                )}
                {runtime.lastError && (
                  <InfoRow label="最近错误" value={<span className="text-red-400 text-xs">{runtime.lastError}</span>} />
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {user && (
        <ConfirmDialog
          open={confirmDialog}
          onOpenChange={setConfirmDialog}
          title={user.status === 'active' ? '禁用用户' : '启用用户'}
          description={`确认要${user.status === 'active' ? '禁用' : '启用'}用户 ${user.userId} 吗？`}
          confirmLabel={user.status === 'active' ? '禁用' : '启用'}
          destructive={user.status === 'active'}
          onConfirm={handleStatusToggle}
        />
      )}
    </div>
  );
}

export function AdminUserDetailPage() {
  return (
    <RequireAdmin>
      <AppShell>
        <UserDetailContent />
      </AppShell>
    </RequireAdmin>
  );
}
