/**
 * ClawLoops Platform - App Router
 * Design: Crafted Dark - Technical Platform
 *
 * Routes per 页面清单与冻结边界.md (v0.5):
 * Public:
 *   /login                   - Login page (inline username/password form)
 *   /invite/:token           - Invitation onboarding (in-page accept flow)
 *   /force-password-change   - Seed admin first-login forced password change
 *
 * User (requires auth):
 *   /app                     - Dashboard (工作台)
 *   /workspace-entry         - Workspace entry (工作区入口)
 *
 * Admin (requires admin role):
 *   /admin                   - Admin home (摘要 + 待办 + 快捷入口)
 *   /admin/users             - User management list
 *   /admin/users/:userId     - User detail
 *   /admin/invitations       - Invitation management
 *   /admin/invitations/:id   - Invitation detail
 *   /admin/models            - Model governance
 *   /admin/provider-credentials - Provider credentials
 *   /admin/usage             - Usage summary
 *
 * System:
 *   /403                     - Forbidden
 *   /disabled                - User disabled
 *   *                        - 404 Not Found
 *
 * Removed in v0.5:
 *   /post-login              - Replaced by inline login form
 *   /error/403               - Renamed to /403
 *   /error/disabled          - Renamed to /disabled
 *   /error/bootstrap         - Removed (bootstrap errors handled in AuthContext)
 */

import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Route, Switch, Redirect } from 'wouter';
import ErrorBoundary from './components/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import ThemeCursor from './components/ThemeCursor';

// Public pages
import LoginPage from './pages/Login';
import InvitePage from './pages/Invite';
import ForcePasswordChangePage from './pages/ForcePasswordChange';

// User pages
import DashboardPage from './pages/Dashboard';
import WorkspaceEntryPage from './pages/WorkspaceEntry';
import FileBrowserPage from './pages/FileBrowser';
import PublicAreaPage from './pages/PublicArea';

// Admin pages
import AdminHomePage from './pages/admin/AdminHome';
import { AdminUsersListPage, AdminUserDetailPage } from './pages/admin/AdminUsers';
import AdminInvitationsPage from './pages/admin/AdminInvitations';
import AdminInvitationDetailPage from './pages/admin/AdminInvitationDetail';
import AdminModelsPage from './pages/admin/AdminModels';
import AdminCredentialsPage from './pages/admin/AdminCredentials';
import AdminUsagePage from './pages/admin/AdminUsage';
import AdminPublicAreaPage from './pages/admin/AdminPublicArea';

// Error pages
import {
  ForbiddenPage,
  UserDisabledPage,
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
      <Route path="/force-password-change" component={ForcePasswordChangePage} />

      {/* User routes */}
      <Route path="/app" component={DashboardPage} />
      <Route path="/workspace-entry" component={WorkspaceEntryPage} />
      <Route path="/file-browser" component={FileBrowserPage} />
      <Route path="/public-area" component={PublicAreaPage} />

      {/* Admin routes */}
      <Route path="/admin" component={AdminHomePage} />
      <Route path="/admin/users" component={AdminUsersListPage} />
      <Route path="/admin/users/:userId" component={AdminUserDetailPage} />
      <Route path="/admin/invitations" component={AdminInvitationsPage} />
      <Route path="/admin/invitations/:invitationId" component={AdminInvitationDetailPage} />
      <Route path="/admin/models" component={AdminModelsPage} />
      <Route path="/admin/provider-credentials" component={AdminCredentialsPage} />
      <Route path="/admin/usage" component={AdminUsagePage} />
      <Route path="/admin/public-area" component={AdminPublicAreaPage} />

      {/* System error routes (v0.5 renamed) */}
      <Route path="/403" component={ForbiddenPage} />
      <Route path="/disabled" component={UserDisabledPage} />

      {/* Legacy error route redirects for backwards compatibility */}
      <Route path="/error/403">
        <Redirect to="/403" />
      </Route>
      <Route path="/error/disabled">
        <Redirect to="/disabled" />
      </Route>

      {/* 404 fallback */}
      <Route component={NotFoundPage} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
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
            <ThemeCursor />
            <Router />
          </TooltipProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
