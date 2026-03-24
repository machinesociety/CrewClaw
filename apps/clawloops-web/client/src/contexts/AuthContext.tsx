/**
 * AuthContext - Global session and access state
 * Design: Crafted Dark - ClawLoops Platform
 *
 * State slices: session, access
 * Per UI_状态模型.md §2.3 and §4.1
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
  | 'authenticatedReady'
  | 'bootstrapFailed';

interface AuthContextValue {
  bootState: AppBootState;
  user: SessionUser | null;
  access: AccessGate | null;
  isAdmin: boolean;
  isAuthenticated: boolean;
  isDisabled: boolean;
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

      setUser(meRes.user);
      setBootState('checkingAccess');

      // Fetch access in parallel (already have user)
      const accessRes = await authApi.access();
      setAccess(accessRes);

      if (!accessRes.allowed && accessRes.reason === 'USER_DISABLED') {
        setBootState('disabledBlocked');
        return;
      }

      setBootState('authenticatedReady');
    } catch (e) {
      if (isAppError(e) && (e.httpStatus === 401 || e.code === 'UNAUTHENTICATED')) {
        setUser(null);
        setAccess(null);
        setBootState('unauthenticated');
      } else if (isAppError(e) && e.httpStatus >= 500) {
        setBootError(isAppError(e) ? e.message : 'Failed to initialize session');
        setBootState('bootstrapFailed');
      } else {
        // Network error or API not available - treat as unauthenticated
        setUser(null);
        setAccess(null);
        setBootState('unauthenticated');
      }
    }
  }, []);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const logout = useCallback(() => {
    setUser(null);
    setAccess(null);
    setBootState('unauthenticated');
    // Redirect to login
    window.location.href = '/login';
  }, []);

  const value: AuthContextValue = {
    bootState,
    user,
    access,
    isAdmin: user?.isAdmin ?? false,
    isAuthenticated: bootState === 'authenticatedReady' || bootState === 'disabledBlocked',
    isDisabled: bootState === 'disabledBlocked',
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
