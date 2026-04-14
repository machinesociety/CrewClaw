/**
 * ClawLoops API Layer
 * Design: Crafted Dark - Technical Platform
 * All calls go to /api/v1/* only. Never call /internal/* from frontend.
 *
 * Based on API_Spec.md v0.5-lightweight-auth-revision
 * Key changes from v0.4:
 * - Login is now inline username/password form (POST /auth/login)
 * - /post-login removed; invitation accept is /public/invitations/{token}/accept
 * - SessionUser gains username, mustChangePassword, passwordChangeReason
 * - AuthOptionsResponse gains passwordPolicy and features
 * - New: LoginRequest, LoginResult, PasswordChangeRequest, PasswordChangeResult
 * - New: InvitationAcceptRequest, InvitationAcceptResult
 */

// ============================================================
// Types (frozen field names per API_Spec.md §12)
// ============================================================

export interface AppError {
  httpStatus: number;
  code: string;
  message: string;
}

export type AsyncResource<T> =
  | { phase: 'idle'; data: null; error: null }
  | { phase: 'loading'; data: T | null; error: null }
  | { phase: 'success'; data: T; error: null }
  | { phase: 'error'; data: T | null; error: AppError };

export type MutationState =
  | { phase: 'idle' }
  | { phase: 'submitting' }
  | { phase: 'success' }
  | { phase: 'error'; error: AppError };

// Auth
export interface SessionUser {
  userId: string;
  subjectId: string;
  username?: string;           // v0.5: preferred login username
  tenantId: string;
  role: 'admin' | 'user';
  status: 'active' | 'disabled';
  auth: {
    provider: string;
    method: string;
  };
  isAdmin: boolean;
  isDisabled: boolean;
  mustChangePassword?: boolean;         // v0.5: true for seed admin first login
  passwordChangeReason?: string | null; // v0.5: reason for forced change
}

export interface AuthMeResponse {
  authenticated: boolean;
  user?: SessionUser;
}

export interface AccessGate {
  allowed: boolean;
  reason: string | null;
}

export interface AuthOption {
  type: string;
  enabled?: boolean;
  label: string;
}

export interface PasswordPolicy {
  minLength: number;
  maxLength: number;
  requireLetter: boolean;
  requireNumber: boolean;
  disallowUsernameAsPassword: boolean;
  disallowDefaultAdminPassword?: boolean;
}

export interface AuthOptionsResponse {
  provider: string;
  methods: AuthOption[];
  passwordPolicy?: PasswordPolicy;
  features?: {
    forcedPasswordChange?: boolean;
    passwordRecovery?: boolean;
    thirdPartyLogin?: boolean;
  };
}

// v0.5: Inline login
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResult {
  redirectTo?: string;           // '/admin' | '/app' | '/force-password-change'
  mustChangePassword?: boolean;
  user?: SessionUser;
}

// v0.5: Forced password change
export interface PasswordChangeRequest {
  currentPassword: string;
  newPassword: string;
  newPasswordConfirm: string;
}

export interface PasswordChangeResult {
  changed: boolean;
  redirectTo?: string;
  user?: SessionUser;
}

export interface LogoutResult {
  ok: boolean;
}

/** @deprecated v0.5: /post-login removed. Kept for type compatibility only. */
export interface PostLoginResult {
  status?: string;
  userId?: string;
  entryType?: 'workspace' | 'admin_console';
  hasWorkspace?: boolean;
  workspaceId?: string | null;
  workspaceName?: string | null;
  needsWorkspaceSelection?: boolean;
  invitationApplied?: boolean;
  redirectTo?: string;
  result?: string;
}

// Invitation
export interface InvitationPreview {
  valid: boolean;
  invitation?: {
    invitationId?: string;
    targetEmail: string;
    loginUsername?: string;  // v0.5: preferred display name; show as primary if present
    workspaceId: string;
    workspaceName: string;
    role: string;
    status: 'pending' | 'consumed' | 'revoked';
    expiresAt: string;
  };
}

/** @deprecated v0.5: /start removed; use /accept instead */
export interface InvitationStartResult {
  status: string;
  pendingInvitationSession?: {
    ttlSeconds: number;
  };
  redirectUrl?: string;
}

// v0.5: In-page accept with password setup
export interface InvitationAcceptRequest {
  username: string;
  password: string;
  passwordConfirm: string;
}

export interface InvitationAcceptResult {
  accepted: boolean;
  replayed?: boolean;          // true = idempotent replay; treat as success
  redirectTo?: string;         // '/app'
  user?: SessionUser;
  workspaceBinding?: {
    workspaceId: string;
    workspaceName: string;
    role: string;
  };
}

// Runtime
export interface RuntimeStatusProjection {
  runtimeId: string;
  desiredState: 'running' | 'stopped' | 'deleted';
  observedState: 'creating' | 'running' | 'stopped' | 'error' | 'deleted';
  task?: {
    status: string;
  };
  ready: boolean;
  browserUrl?: string;
  reason?: string | null;
  lastError?: string | null;
}

export interface RuntimeBinding {
  runtimeId: string;
  volumeId: string;
  imageRef: string;
  desiredState: string;
  observedState: string;
  browserUrl?: string;
  internalEndpoint?: string;
  retentionPolicy: string;
  lastError?: string | null;
}

export interface RuntimeTask {
  taskId: string;
  userId: string;
  runtimeId: string;
  action: 'ensure_running' | 'stop' | 'delete';
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'canceled';
  message?: string;
}

export interface WorkspaceEntry {
  ready: boolean;
  hasWorkspace?: boolean;
  runtimeId?: string;
  browserUrl?: string;
  reason?: string | null;
}

export interface RuntimeActionResponse {
  taskId: string;
  action: string;
  status: string;
}

// Models
export interface Model {
  modelId: string;
  name: string;
  provider?: string;
  pricingType?: 'free' | 'paid';
  enabled?: boolean;
  /**
   * Admin models API currently uses `userVisible`.
   * Keep `visible` for backward compatibility with older payloads/UI code.
   */
  visible?: boolean;
  userVisible?: boolean;
  isDefault?: boolean;
  policy?: Record<string, unknown>;
}

// Admin - Users
export interface AdminUser {
  userId: string;
  subjectId: string;
  role: string;
  status: 'active' | 'disabled';
  authMethod: string;
  runtimeObservedState?: string;
  lastLoginAt?: string;
  email?: string;
  username?: string;
}

export interface AdminUserDetail extends AdminUser {
  tenantId?: string;
  createdAt?: string;
}

// Admin - Invitations
export interface AdminInvitation {
  invitationId: string;
  targetEmail: string;
  loginUsername?: string;  // preferred login username for no-real-email users
  workspaceId: string;
  role: string;
  status: 'pending' | 'consumed' | 'revoked';
  expiresAt: string;
  consumedAt?: string;
  consumedByUserId?: string;
  lastError?: string;
  createdAt?: string;
}

export interface CreateInvitationRequest {
  targetEmail: string;
  loginUsername?: string;  // optional: preferred login username
  workspaceId: string;
  role: string;
  expiresInHours: number;
}

// Admin - Provider Credentials
export interface ProviderCredential {
  credentialId: string;
  provider: string;
  name?: string;
  status?: 'valid' | 'invalid' | 'unverified';
  lastVerifiedAt?: string;
  createdAt?: string;
}

export interface CreateCredentialRequest {
  provider: string;
  name?: string;
  apiKey?: string;
  [key: string]: unknown;
}

// Admin - Home
export interface AdminHomeSummary {
  totalUsers: number;
  activeUsers: number;
  disabledUsers: number;
  pendingInvitations: number;
  expiringInvitations24h: number;
  runningRuntimes: number;
  runtimeErrors: number;
}

export interface AdminHomePendingInvitation {
  invitationId: string;
  targetEmail: string;
  loginUsername?: string;
  workspaceId: string;
  role: string;
  expiresAt: string;
  status: 'pending' | 'consumed' | 'revoked';
}

export interface AdminHomeRuntimeAlert {
  userId: string;
  runtimeId: string;
  observedState: string;
  lastError?: string | null;
  updatedAt?: string;
}

export interface AdminHome {
  summary: AdminHomeSummary;
  attention: {
    pendingInvitations: AdminHomePendingInvitation[];
    runtimeAlerts: AdminHomeRuntimeAlert[];
  };
}

// Admin - Usage
export interface UsageSummary {
  totalRequests?: number;
  totalTokens?: number;
  totalCost?: number;
  byModel?: Array<{
    modelId: string;
    modelName?: string;
    requests: number;
    tokens: number;
  }>;
  byUser?: Array<{
    userId: string;
    requests: number;
    tokens: number;
  }>;
  period?: {
    from: string;
    to: string;
  };
}

// ============================================================
// HTTP Client
// ============================================================

const BASE_URL = '/api/v1';

async function request<T>(
  method: string,
  path: string,
  body?: unknown
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let errorData: { code?: string; message?: string } = {};
    try {
      errorData = await res.json();
    } catch {
      // ignore parse error
    }
    const err: AppError = {
      httpStatus: res.status,
      code: errorData.code || 'UNKNOWN_ERROR',
      message: errorData.message || `HTTP ${res.status}`,
    };
    throw err;
  }

  // 204 No Content
  if (res.status === 204) {
    return undefined as T;
  }

  // Check content-type: if HTML returned (SPA fallback), treat as unauthenticated
  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    const err: AppError = {
      httpStatus: 401,
      code: 'UNAUTHENTICATED',
      message: 'API not available',
    };
    throw err;
  }

  return res.json() as Promise<T>;
}

const get = <T>(path: string) => request<T>('GET', path);
const post = <T>(path: string, body?: unknown) => request<T>('POST', path, body);
const put = <T>(path: string, body?: unknown) => request<T>('PUT', path, body);
const patch = <T>(path: string, body?: unknown) => request<T>('PATCH', path, body);
const del = <T>(path: string) => request<T>('DELETE', path);

// ============================================================
// Auth API
// ============================================================

export const authApi = {
  me: () => get<AuthMeResponse>('/auth/me'),
  access: () => get<AccessGate>('/auth/access'),
  options: () => get<AuthOptionsResponse>('/auth/options'),
  /** v0.5: inline username/password login */
  login: (data: LoginRequest) => post<LoginResult>('/auth/login', data),
  /** v0.12: revoke server-side session and clear cookie */
  logout: () => post<LogoutResult>('/auth/logout'),
  /** v0.5: forced password change for seed admin first login */
  changePassword: (data: PasswordChangeRequest) =>
    post<PasswordChangeResult>('/auth/password/change', data),
  /** @deprecated v0.5: use login() instead */
  postLogin: (body?: { pendingInvitationSessionId?: string }) =>
    post<PostLoginResult>('/auth/post-login', body || {}),
};

// ============================================================
// Public Invitation API
// ============================================================

export const invitationPublicApi = {
  preview: (token: string) =>
    get<InvitationPreview>(`/public/invitations/${token}`),
  /** v0.5: in-page accept with username + password setup */
  accept: (token: string, data: InvitationAcceptRequest) =>
    post<InvitationAcceptResult>(`/public/invitations/${token}/accept`, data),
  /** @deprecated v0.5: /start removed */
  start: (token: string) =>
    post<InvitationStartResult>(`/public/invitations/${token}/start`),
};

// ============================================================
// User Runtime API
// ============================================================

export const runtimeApi = {
  status: () => get<RuntimeStatusProjection>('/users/me/runtime/status'),
  full: () => get<{ userId: string; runtime: RuntimeBinding }>('/users/me/runtime'),
  start: () => post<RuntimeActionResponse>('/users/me/runtime/start'),
  stop: () => post<RuntimeActionResponse>('/users/me/runtime/stop'),
  delete: (retentionPolicy: 'preserve_workspace' | 'wipe_workspace') =>
    post<RuntimeActionResponse>('/users/me/runtime/delete', { retentionPolicy }),
  getTask: (taskId: string) => get<RuntimeTask>(`/runtime/tasks/${taskId}`),
};

// ============================================================
// Workspace Entry API
// ============================================================

export const workspaceApi = {
  entry: () => get<WorkspaceEntry>('/workspace-entry'),
};

// ============================================================
// Models API (user-facing, read-only)
// ============================================================

export const modelsApi = {
  list: () => get<{ models: Model[] }>('/models'),
};

// ============================================================
// Admin API
// ============================================================

export const adminApi = {
  // Home
  home: () => get<AdminHome>('/admin/home'),

  // Users
  users: {
    list: () => get<{ users: AdminUser[] }>('/admin/users'),
    get: (userId: string) => get<AdminUserDetail>(`/admin/users/${userId}`),
    updateStatus: (userId: string, status: 'active' | 'disabled') =>
      patch<AdminUserDetail>(`/admin/users/${userId}/status`, { status }),
    getRuntime: (userId: string) =>
      get<{ runtime: RuntimeBinding }>(`/admin/users/${userId}/runtime`),
  },

  // Invitations
  invitations: {
    list: () => get<{ invitations: AdminInvitation[] }>('/admin/invitations'),
    get: (invitationId: string) =>
      get<AdminInvitation>(`/admin/invitations/${invitationId}`),
    create: (data: CreateInvitationRequest) =>
      post<AdminInvitation>('/admin/invitations', data),
    revoke: (invitationId: string) =>
      post<void>(`/admin/invitations/${invitationId}/revoke`),
    resend: (invitationId: string) =>
      post<void>(`/admin/invitations/${invitationId}/resend`),
  },

  // Models
  models: {
    list: () => get<{ models: Model[] }>('/admin/models'),
    update: (modelId: string, data: Partial<Model>) =>
      put<Model>(`/admin/models/${modelId}`, data),
    syncOpenRouter: () =>
      post<{ fetched: number; created: number; updated: number }>(
        '/admin/models/sync/openrouter',
        {}
      ),
  },

  // Provider Credentials
  credentials: {
    list: () => get<{ credentials: ProviderCredential[] }>('/admin/provider-credentials'),
    create: (data: CreateCredentialRequest) =>
      post<ProviderCredential>('/admin/provider-credentials', data),
    verify: (credentialId: string) =>
      post<{ status: string }>(`/admin/provider-credentials/${credentialId}/verify`),
    delete: (credentialId: string) =>
      del<void>(`/admin/provider-credentials/${credentialId}`),
  },

  // Usage
  usage: {
    summary: () => get<UsageSummary>('/admin/usage/summary'),
  },
};

// ============================================================
// Error helpers
// ============================================================

export function isAppError(e: unknown): e is AppError {
  return (
    typeof e === 'object' &&
    e !== null &&
    'code' in e &&
    'httpStatus' in e
  );
}

export function getErrorCode(e: unknown): string {
  if (isAppError(e)) return e.code;
  return 'UNKNOWN_ERROR';
}

export function getErrorMessage(e: unknown): string {
  if (isAppError(e)) return e.message;
  if (e instanceof Error) return e.message;
  return 'An unexpected error occurred';
}

// ============================================================
// Polling utilities
// ============================================================

export interface PollOptions {
  intervalMs?: number;
  maxMs?: number;
  onTick?: (result: RuntimeTask) => void;
  onTimeout?: () => void;
}

/**
 * Poll runtime task until terminal state or timeout.
 * Terminal states: succeeded | failed | canceled
 * Strategy: first 10s every 2s, then every 3s, max 90s
 */
export async function pollRuntimeTask(
  taskId: string,
  options: PollOptions = {}
): Promise<RuntimeTask | null> {
  const { onTick, onTimeout } = options;
  const maxMs = options.maxMs ?? 90_000;
  const start = Date.now();

  const terminalStates = new Set(['succeeded', 'failed', 'canceled']);

  const getInterval = (elapsed: number) => (elapsed < 10_000 ? 2_000 : 3_000);

  return new Promise((resolve) => {
    let timeoutId: ReturnType<typeof setTimeout>;

    const tick = async () => {
      const elapsed = Date.now() - start;
      if (elapsed >= maxMs) {
        onTimeout?.();
        resolve(null);
        return;
      }

      try {
        const task = await runtimeApi.getTask(taskId);
        onTick?.(task);

        if (terminalStates.has(task.status)) {
          resolve(task);
          return;
        }

        timeoutId = setTimeout(tick, getInterval(elapsed));
      } catch {
        // On error, keep polling unless timed out
        timeoutId = setTimeout(tick, getInterval(elapsed));
      }
    };

    tick();

    // Return cancel function via resolve(null) on cleanup
    return () => clearTimeout(timeoutId);
  });
}

/**
 * Poll workspace-entry until ready or timeout.
 * Strategy: every 2s, max 60s
 */
export async function pollWorkspaceEntry(
  onTick: (entry: WorkspaceEntry) => void,
  onTimeout: () => void
): Promise<WorkspaceEntry | null> {
  const maxMs = 60_000;
  const start = Date.now();

  return new Promise((resolve) => {
    let timeoutId: ReturnType<typeof setTimeout>;

    const tick = async () => {
      const elapsed = Date.now() - start;
      if (elapsed >= maxMs) {
        onTimeout();
        resolve(null);
        return;
      }

      try {
        const entry = await workspaceApi.entry();
        onTick(entry);

        if (entry.ready) {
          resolve(entry);
          return;
        }

        timeoutId = setTimeout(tick, 2_000);
      } catch {
        timeoutId = setTimeout(tick, 2_000);
      }
    };

    tick();
    return () => clearTimeout(timeoutId);
  });
}
