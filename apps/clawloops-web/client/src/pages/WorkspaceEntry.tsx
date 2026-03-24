/**
 * WorkspaceEntry Page - /workspace-entry
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Per 页面调用流程_BFF编排.md §5.2 and UI_状态模型.md §4.4
 * State machine: loadingEntry → readyToRedirect/runtimeNotReady/noWorkspace/entryFailed
 * Polls workspace-entry every 2s, max 60s
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation } from 'wouter';
import { workspaceApi, WorkspaceEntry, isAppError } from '@/lib/api';
import { RequireAuth } from '@/components/guards/RouteGuard';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/button';
import { MonoText } from '@/components/shared/PageComponents';
import {
  Loader2,
  ExternalLink,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowLeft,
} from 'lucide-react';
import { Link } from 'wouter';

// ============================================================
// State machine
// ============================================================

type WorkspaceEntryState =
  | 'loadingEntry'
  | 'readyToRedirect'
  | 'runtimeNotReady'
  | 'noWorkspace'
  | 'entryFailed'
  | 'timedOut';

// ============================================================
// Main component
// ============================================================

function WorkspaceEntryContent() {
  const [, navigate] = useLocation();
  const [pageState, setPageState] = useState<WorkspaceEntryState>('loadingEntry');
  const [entry, setEntry] = useState<WorkspaceEntry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [isPolling, setIsPolling] = useState(false);

  const pollingRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startTimeRef = useRef<number>(0);
  const MAX_POLL_MS = 60_000;
  const POLL_INTERVAL_MS = 2_000;

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearTimeout(pollingRef.current);
      pollingRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const loadEntry = useCallback(async (): Promise<boolean> => {
    try {
      const data = await workspaceApi.entry();
      setEntry(data);

      if (data.ready) {
        setPageState('readyToRedirect');
        // Immediately redirect
        if (data.browserUrl) {
          window.location.href = data.browserUrl;
        }
        return true; // done
      }

      if (!data.runtimeId) {
        setPageState('noWorkspace');
        return true; // done
      }

      setPageState('runtimeNotReady');
      return false; // keep polling
    } catch (e) {
      if (isAppError(e)) {
        if (e.code === 'USER_DISABLED') {
          navigate('/error/disabled');
          return true;
        }
        setError(e.message);
        setErrorCode(e.code);
      } else {
        setError('加载工作区入口失败');
        setErrorCode(null);
      }
      setPageState('entryFailed');
      return true; // done (with error)
    }
  }, [navigate]);

  const startPolling = useCallback(async () => {
    stopPolling();
    setIsPolling(true);
    startTimeRef.current = Date.now();
    setElapsed(0);

    const tick = async () => {
      const now = Date.now();
      const elapsed = now - startTimeRef.current;
      setElapsed(Math.floor(elapsed / 1000));

      if (elapsed >= MAX_POLL_MS) {
        setPageState('timedOut');
        setIsPolling(false);
        return;
      }

      const done = await loadEntry();
      if (!done) {
        pollingRef.current = setTimeout(tick, POLL_INTERVAL_MS);
      } else {
        setIsPolling(false);
      }
    };

    tick();
  }, [loadEntry, stopPolling]);

  useEffect(() => {
    startPolling();
    return () => stopPolling();
  }, []);

  const handleManualRefresh = () => {
    startPolling();
  };

  const remainingSeconds = Math.max(0, 60 - elapsed);

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="w-full max-w-md text-center">

        {/* Loading / Polling */}
        {(pageState === 'loadingEntry' || pageState === 'runtimeNotReady') && (
          <div className="bg-card border border-border rounded-xl p-10">
            <div className="w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center mx-auto mb-5">
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
            </div>
            <h2 className="text-lg font-semibold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
              {pageState === 'loadingEntry' ? '正在检查工作区...' : '环境准备中'}
            </h2>
            <p className="text-sm text-muted-foreground mb-4">
              {pageState === 'runtimeNotReady'
                ? 'Runtime 正在启动，请稍候...'
                : '正在获取工作区入口信息...'}
            </p>

            {isPolling && pageState === 'runtimeNotReady' && (
              <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                <Clock className="w-3.5 h-3.5" />
                <span>自动检查中，剩余 {remainingSeconds}s</span>
              </div>
            )}

            {entry?.runtimeId && (
              <div className="mt-4 pt-4 border-t border-border">
                <MonoText>{entry.runtimeId}</MonoText>
              </div>
            )}
          </div>
        )}

        {/* Ready - redirecting */}
        {pageState === 'readyToRedirect' && (
          <div className="bg-card border border-border rounded-xl p-10">
            <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-5">
              <CheckCircle2 className="w-8 h-8 text-green-400" />
            </div>
            <h2 className="text-lg font-semibold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
              工作区已就绪
            </h2>
            <p className="text-sm text-muted-foreground mb-4">正在跳转到工作区...</p>
            {entry?.browserUrl && (
              <a
                href={entry.browserUrl}
                className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                手动跳转
              </a>
            )}
          </div>
        )}

        {/* No workspace */}
        {pageState === 'noWorkspace' && (
          <div className="bg-card border border-border rounded-xl p-10">
            <div className="w-16 h-16 rounded-full bg-yellow-500/10 flex items-center justify-center mx-auto mb-5">
              <AlertCircle className="w-8 h-8 text-yellow-400" />
            </div>
            <h2 className="text-lg font-semibold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
              暂无工作区
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              您的账号尚未绑定工作区，请联系管理员。
            </p>
            <Link href="/app">
              <Button variant="outline" size="sm" className="gap-2">
                <ArrowLeft className="w-3.5 h-3.5" />
                返回工作台
              </Button>
            </Link>
          </div>
        )}

        {/* Timed out */}
        {pageState === 'timedOut' && (
          <div className="bg-card border border-border rounded-xl p-10">
            <div className="w-16 h-16 rounded-full bg-yellow-500/10 flex items-center justify-center mx-auto mb-5">
              <Clock className="w-8 h-8 text-yellow-400" />
            </div>
            <h2 className="text-lg font-semibold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
              等待超时
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              Runtime 启动时间过长，请手动刷新或返回工作台检查状态。
            </p>
            <div className="flex gap-2 justify-center">
              <Button size="sm" className="gap-2" onClick={handleManualRefresh}>
                <RefreshCw className="w-3.5 h-3.5" />
                手动刷新
              </Button>
              <Link href="/app">
                <Button variant="outline" size="sm" className="gap-2">
                  <ArrowLeft className="w-3.5 h-3.5" />
                  返回工作台
                </Button>
              </Link>
            </div>
          </div>
        )}

        {/* Error */}
        {pageState === 'entryFailed' && (
          <div className="bg-card border border-border rounded-xl p-10">
            <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-5">
              <AlertCircle className="w-8 h-8 text-red-400" />
            </div>
            <h2 className="text-lg font-semibold text-foreground mb-2" style={{ fontFamily: 'Space Grotesk' }}>
              加载失败
            </h2>
            <p className="text-sm text-muted-foreground mb-1">{error}</p>
            {errorCode && <MonoText className="block mb-6">{errorCode}</MonoText>}
            <div className="flex gap-2 justify-center">
              <Button size="sm" className="gap-2" onClick={handleManualRefresh}>
                <RefreshCw className="w-3.5 h-3.5" />
                重试
              </Button>
              <Link href="/app">
                <Button variant="outline" size="sm" className="gap-2">
                  <ArrowLeft className="w-3.5 h-3.5" />
                  返回工作台
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function WorkspaceEntryPage() {
  return (
    <RequireAuth>
      <AppShell>
        <WorkspaceEntryContent />
      </AppShell>
    </RequireAuth>
  );
}
