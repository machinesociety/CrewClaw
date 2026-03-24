/**
 * ClawLoops Platform - App Router
 * Design: Crafted Dark - Technical Platform
 *
 * Routes per 页面清单与冻结边界.md:
 * Public:
 *   /login                  - Login page
 *   /invite/:token          - Invitation onboarding
 *   /post-login             - Post-Authentik callback
 *
 * User (requires auth):
 *   /app                    - Dashboard (工作台)
 *   /workspace-entry        - Workspace entry (工作区入口)
 *
 * Admin (requires admin role):
 *   /admin/users            - User management list
 *   /admin/users/:userId    - User detail
 *   /admin/invitations      - Invitation management
 *   /admin/models           - Model governance
 *   /admin/provider-credentials - Provider credentials
 *   /admin/usage            - Usage summary
 *
 * System:
 *   /error/403              - Forbidden
 *   /error/disabled         - User disabled
 *   /error/bootstrap        - Bootstrap failed
 *   *                       - 404 Not Found
 */

import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Route, Switch, Redirect } from 'wouter';
import ErrorBoundary from './components/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';

// Public pages
import LoginPage from './pages/Login';
import InvitePage from './pages/Invite';
import PostLoginPage from './pages/PostLogin';

// User pages
import DashboardPage from './pages/Dashboard';
import WorkspaceEntryPage from './pages/WorkspaceEntry';

// Admin pages
import { AdminUsersListPage, AdminUserDetailPage } from './pages/admin/AdminUsers';
import AdminInvitationsPage from './pages/admin/AdminInvitations';
import AdminModelsPage from './pages/admin/AdminModels';
import AdminCredentialsPage from './pages/admin/AdminCredentials';
import AdminUsagePage from './pages/admin/AdminUsage';

// Error pages
import {
  ForbiddenPage,
  UserDisabledPage,
  BootstrapFailedPage,
  NotFoundPage,
} from './pages/ErrorPages';

function Router() {
  return (
    <Switch>
      {/* Root redirect */}
      <Route path="/">
        <Redirect to="/app" />
      </Route>

      {/* Public routes */}
      <Route path="/login" component={LoginPage} />
      <Route path="/invite/:token" component={InvitePage} />
      <Route path="/post-login" component={PostLoginPage} />

      {/* User routes */}
      <Route path="/app" component={DashboardPage} />
      <Route path="/workspace-entry" component={WorkspaceEntryPage} />

      {/* Admin routes */}
      <Route path="/admin/users" component={AdminUsersListPage} />
      <Route path="/admin/users/:userId" component={AdminUserDetailPage} />
      <Route path="/admin/invitations" component={AdminInvitationsPage} />
      <Route path="/admin/models" component={AdminModelsPage} />
      <Route path="/admin/provider-credentials" component={AdminCredentialsPage} />
      <Route path="/admin/usage" component={AdminUsagePage} />

      {/* System error routes */}
      <Route path="/error/403" component={ForbiddenPage} />
      <Route path="/error/disabled" component={UserDisabledPage} />
      <Route path="/error/bootstrap" component={BootstrapFailedPage} />

      {/* 404 fallback */}
      <Route component={NotFoundPage} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="dark">
        <AuthProvider>
          <TooltipProvider>
            <Toaster
              position="top-right"
              toastOptions={{
                style: {
                  background: 'oklch(0.16 0.008 264)',
                  border: '1px solid oklch(1 0 0 / 0.08)',
                  color: 'oklch(0.92 0.005 264)',
                },
              }}
            />
            <Router />
          </TooltipProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
