/**
 * RouteGuard - Route-level access control
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Implements the application startup state machine per UI_状态模型.md §4.1
 */

import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';
import { Redirect } from 'wouter';

interface GuardProps {
  children: React.ReactNode;
}

// Full-page loading skeleton
function BootingScreen() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
            <span className="text-primary font-bold text-sm" style={{ fontFamily: 'Space Grotesk' }}>CL</span>
          </div>
          <span className="text-foreground font-semibold text-lg" style={{ fontFamily: 'Space Grotesk' }}>
            ClawLoops
          </span>
        </div>
        <Loader2 className="w-5 h-5 text-muted-foreground animate-spin" />
        <p className="text-muted-foreground text-sm">正在初始化...</p>
      </div>
    </div>
  );
}

/**
 * RequireAuth - Requires authenticated + allowed user
 * Redirects to /login if unauthenticated
 * Shows disabled page if USER_DISABLED
 */
export function RequireAuth({ children }: GuardProps) {
  const { bootState } = useAuth();

  if (bootState === 'booting' || bootState === 'checkingSession' || bootState === 'checkingAccess') {
    return <BootingScreen />;
  }

  if (bootState === 'unauthenticated') {
    return <Redirect to="/login" />;
  }

  if (bootState === 'disabledBlocked') {
    return <Redirect to="/error/disabled" />;
  }

  if (bootState === 'bootstrapFailed') {
    return <Redirect to="/error/bootstrap" />;
  }

  return <>{children}</>;
}

/**
 * RequireAdmin - Requires admin role
 * Redirects to /error/403 if not admin
 */
export function RequireAdmin({ children }: GuardProps) {
  const { bootState, isAdmin } = useAuth();

  if (bootState === 'booting' || bootState === 'checkingSession' || bootState === 'checkingAccess') {
    return <BootingScreen />;
  }

  if (bootState === 'unauthenticated') {
    return <Redirect to="/login" />;
  }

  if (bootState === 'disabledBlocked') {
    return <Redirect to="/error/disabled" />;
  }

  if (bootState === 'bootstrapFailed') {
    return <Redirect to="/error/bootstrap" />;
  }

  if (!isAdmin) {
    return <Redirect to="/error/403" />;
  }

  return <>{children}</>;
}

/**
 * RedirectIfAuthenticated - For public pages like /login
 * Redirects to /app if already authenticated
 */
export function RedirectIfAuthenticated({ children }: GuardProps) {
  const { bootState } = useAuth();

  if (bootState === 'booting' || bootState === 'checkingSession') {
    return <BootingScreen />;
  }

  if (bootState === 'authenticatedReady') {
    return <Redirect to="/app" />;
  }

  return <>{children}</>;
}
