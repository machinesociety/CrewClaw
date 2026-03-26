/**
 * AuthContext - Global session and access state
 * Design: Crafted Dark - ClawLoops Platform
 *
 * v0.5 Guard order (per UI_状态模型.md §5 and 页面调用流程_BFF编排.md §4):
 *   1. GET /auth/me  → unauthenticated | mustChangePassword | checkingAccess
 *   2. GET /auth/access → disabledBlocked | passwordChangeRequired | authenticatedReady
 *
 * New states vs v0.4:
 *   - mustChangePasswordBlocked: user is authenticated but must change password first
 *   - Removed: bootstrapFailed (network errors now → unauthenticated)
 */

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { authApi, AccessGate, SessionUser, isAppError } from '@/lib/api';

// ============================================================
// Types
// ============================================================

export type AppBootState =
  | 'booting'
  | 'checkingSession'
  | 'unauthenticated'
  | 'checkingAccess'
  | 'disabledBlocked'
  | 'mustChangePasswordBlocked'   // v0.5: seed admin first login
  | 'authenticatedReady';

interface AuthContextValue {
  bootState: AppBootState;
  user: SessionUser | null;
  access: AccessGate | null;
  isAdmin: boolean;
  isAuthenticated: boolean;
  isDisabled: boolean;
  mustChangePassword: boolean;    // v0.5: true when forced password change required
  bootError: string | null;
  refresh: () => Promise<void>;
  logout: () => void;
}

// ============================================================
// Context
// ============================================================

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [bootState, setBootState] = useState<AppBootState>('booting');
  const [user, setUser] = useState<SessionUser | null>(null);
  const [access, setAccess] = useState<AccessGate | null>(null);
  const [bootError, setBootError] = useState<string | null>(null);

  const bootstrap = useCallback(async () => {
    setBootState('checkingSession');
    setBootError(null);

    try {
      const meRes = await authApi.me();

      if (!meRes.authenticated || !meRes.user) {
        setUser(null);
        setAccess(null);
        setBootState('unauthenticated');
        return;
      }

      const sessionUser = meRes.user;
      setUser(sessionUser);

      // v0.5 Guard step 1: mustChangePassword check
      // Per UI_状态模型.md §3.1 and §5.3: if mustChangePassword=true, block all business pages
      if (sessionUser.mustChangePassword) {
        setBootState('mustChangePasswordBlocked');
        return;
      }

      setBootState('checkingAccess');

      // v0.5 Guard step 2: access check
      const accessRes = await authApi.access();
      setAccess(accessRes);

      if (!accessRes.allowed) {
        if (accessRes.reason === 'USER_DISABLED') {
          setBootState('disabledBlocked');
          return;
        }
        if (accessRes.reason === 'PASSWORD_CHANGE_REQUIRED') {
          // access gate also signals forced password change
          setBootState('mustChangePasswordBlocked');
          return;
        }
        // Other access denied reasons → treat as unauthenticated
        setUser(null);
        setAccess(null);
        setBootState('unauthenticated');
        return;
      }

      setBootState('authenticatedReady');
    } catch (e) {
      if (isAppError(e) && (e.httpStatus === 401 || e.code === 'UNAUTHENTICATED')) {
        setUser(null);
        setAccess(null);
        setBootState('unauthenticated');
      } else {
        // Network error, API not available, or 5xx → treat as unauthenticated
        // (v0.5 removes bootstrapFailed state; login page handles retry)
        setUser(null);
        setAccess(null);
        setBootState('unauthenticated');
      }
    }
  }, []);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // ignore logout failure; still clear client state
    }
    setUser(null);
    setAccess(null);
    setBootState('unauthenticated');
    window.location.href = '/login';
  }, []);

  const value: AuthContextValue = {
    bootState,
    user,
    access,
    isAdmin: user?.isAdmin ?? false,
    isAuthenticated: bootState === 'authenticatedReady',
    isDisabled: bootState === 'disabledBlocked',
    mustChangePassword: bootState === 'mustChangePasswordBlocked',
    bootError,
    refresh: bootstrap,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
