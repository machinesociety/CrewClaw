/**
 * RouteGuard - Route-level access control
 * Design: Crafted Dark - ClawLoops Platform
 *
 * v0.5 Guard order (per UI_状态模型.md §5 and 页面调用流程_BFF编排.md):
 *   1. Is user authenticated? → /login
 *   2. mustChangePassword=true? → /force-password-change
 *   3. allowed=false (USER_DISABLED)? → /disabled
 *   4. isAdmin required? → /403
 *
 * Route changes from v0.4:
 *   - /error/disabled → /disabled
 *   - /error/403     → /403
 *   - /error/bootstrap removed (network errors → /login)
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
 * RequireAuth - Requires authenticated + allowed user (non-admin pages like /app, /workspace-entry)
 *
 * Guard order:
 *   booting/checking → loading screen
 *   unauthenticated  → /login
 *   mustChangePassword → /force-password-change
 *   disabledBlocked  → /disabled
 *   authenticatedReady → render children
 */
export function RequireAuth({ children }: GuardProps) {
  const { bootState } = useAuth();

  if (bootState === 'booting' || bootState === 'checkingSession' || bootState === 'checkingAccess') {
    return <BootingScreen />;
  }

  if (bootState === 'unauthenticated') {
    return <Redirect to="/login" />;
  }

  // v0.5: mustChangePassword blocks all business pages
  if (bootState === 'mustChangePasswordBlocked') {
    return <Redirect to="/force-password-change" />;
  }

  if (bootState === 'disabledBlocked') {
    return <Redirect to="/disabled" />;
  }

  return <>{children}</>;
}

/**
 * RequireAdmin - Requires admin role (for /admin/* pages)
 *
 * Guard order:
 *   booting/checking → loading screen
 *   unauthenticated  → /login
 *   mustChangePassword → /force-password-change
 *   disabledBlocked  → /disabled
 *   !isAdmin         → /403
 *   authenticatedReady + isAdmin → render children
 */
export function RequireAdmin({ children }: GuardProps) {
  const { bootState, isAdmin } = useAuth();

  if (bootState === 'booting' || bootState === 'checkingSession' || bootState === 'checkingAccess') {
    return <BootingScreen />;
  }

  if (bootState === 'unauthenticated') {
    return <Redirect to="/login" />;
  }

  // v0.5: mustChangePassword blocks admin pages too
  if (bootState === 'mustChangePasswordBlocked') {
    return <Redirect to="/force-password-change" />;
  }

  if (bootState === 'disabledBlocked') {
    return <Redirect to="/disabled" />;
  }

  if (!isAdmin) {
    return <Redirect to="/403" />;
  }

  return <>{children}</>;
}

/**
 * RequireForcePasswordChange - Only for /force-password-change page
 * Allows mustChangePasswordBlocked users; redirects others to their home
 */
export function RequireForcePasswordChange({ children }: GuardProps) {
  const { bootState, isAdmin } = useAuth();

  if (bootState === 'booting' || bootState === 'checkingSession' || bootState === 'checkingAccess') {
    return <BootingScreen />;
  }

  if (bootState === 'unauthenticated') {
    return <Redirect to="/login" />;
  }

  // Only mustChangePasswordBlocked users should be here
  if (bootState === 'mustChangePasswordBlocked') {
    return <>{children}</>;
  }

  // Already authenticated and no password change needed → go to home
  if (bootState === 'authenticatedReady') {
    return <Redirect to={isAdmin ? '/admin' : '/app'} />;
  }

  if (bootState === 'disabledBlocked') {
    return <Redirect to="/disabled" />;
  }

  return <>{children}</>;
}

/**
 * RedirectIfAuthenticated - For public pages like /login
 * v0.5: Redirects admin → /admin, user → /app, mustChangePassword → /force-password-change
 */
export function RedirectIfAuthenticated({ children }: GuardProps) {
  const { bootState, isAdmin } = useAuth();

  if (bootState === 'booting' || bootState === 'checkingSession') {
    return <BootingScreen />;
  }

  if (bootState === 'mustChangePasswordBlocked') {
    return <Redirect to="/force-password-change" />;
  }

  if (bootState === 'authenticatedReady') {
    return <Redirect to={isAdmin ? '/admin' : '/app'} />;
  }

  return <>{children}</>;
}
