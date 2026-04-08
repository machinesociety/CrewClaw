/**
 * AppShell - Main application layout with sidebar
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Layout: 260px fixed sidebar (dark) + scrollable content area
 * Navigation: User section (工作台, 工作区入口) + Admin section (if admin)
 */

import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import { Link, useLocation } from 'wouter';
import {
  LayoutDashboard,
  ExternalLink,
  Users,
  Mail,
  Cpu,
  Key,
  BarChart3,
  LogOut,
  ChevronRight,
  Settings,
  Home,
  FolderOpen,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

// ============================================================
// Nav item types
// ============================================================

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const userNavItems: NavItem[] = [
  { label: '工作台', href: '/app', icon: LayoutDashboard },
  { label: '工作区入口', href: '/workspace-entry', icon: ExternalLink },
  { label: '文件浏览器', href: '/file-browser', icon: FolderOpen },
  { label: '技能', href: '/skills', icon: Sparkles },
];

const adminNavItems: NavItem[] = [
  { label: '管理首页', href: '/admin', icon: Home },
  { label: '用户管理', href: '/admin/users', icon: Users },
  { label: '邀请管理', href: '/admin/invitations', icon: Mail },
  { label: '模型治理', href: '/admin/models', icon: Cpu },
  { label: 'Provider 凭据', href: '/admin/provider-credentials', icon: Key },
  { label: 'Usage 汇总', href: '/admin/usage', icon: BarChart3 },
  { label: '技能管理', href: '/admin/skills', icon: Sparkles },
];

// ============================================================
// NavItem component
// ============================================================

function NavLink({ item }: { item: NavItem }) {
  const [location] = useLocation();
  // For /admin, only exact match to avoid highlighting on all /admin/* sub-pages
  const isActive =
    item.href === '/admin'
      ? location === '/admin'
      : location === item.href || location.startsWith(item.href + '/');

  return (
    <Link href={item.href}>
      <div
        className={cn(
          'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-all duration-150 cursor-pointer group',
          isActive
            ? 'bg-primary/10 text-primary border-l-2 border-primary pl-[10px]'
            : 'text-sidebar-foreground/70 hover:bg-white/5 hover:text-sidebar-foreground border-l-2 border-transparent pl-[10px]'
        )}
      >
        <item.icon className={cn('w-4 h-4 flex-shrink-0', isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground')} />
        <span className="truncate">{item.label}</span>
        {isActive && <ChevronRight className="w-3 h-3 ml-auto text-primary/60" />}
      </div>
    </Link>
  );
}

// ============================================================
// Sidebar
// ============================================================

function Sidebar() {
  const { user, isAdmin, logout } = useAuth();

  const initials = user?.userId
    ? user.userId.slice(0, 2).toUpperCase()
    : 'CL';

  return (
    <aside className="w-64 flex-shrink-0 bg-sidebar border-r border-sidebar-border flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="h-14 flex items-center px-4 border-b border-sidebar-border">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-primary/20 flex items-center justify-center">
            <span className="text-primary font-bold text-xs" style={{ fontFamily: 'Space Grotesk' }}>CL</span>
          </div>
          <span className="font-semibold text-sidebar-foreground" style={{ fontFamily: 'Space Grotesk' }}>
            ClawLoops
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {/* User section */}
        <div className="mb-4">
          <p className="text-xs font-medium text-muted-foreground/60 uppercase tracking-wider px-3 mb-2">
            用户
          </p>
          {userNavItems.map((item) => (
            <NavLink key={item.href} item={item} />
          ))}
        </div>

        {/* Admin section */}
        {isAdmin && (
          <div>
            <p className="text-xs font-medium text-muted-foreground/60 uppercase tracking-wider px-3 mb-2">
              管理员
            </p>
            {adminNavItems.map((item) => (
              <NavLink key={item.href} item={item} />
            ))}
          </div>
        )}
      </nav>

      {/* User footer */}
      <div className="border-t border-sidebar-border p-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="w-full flex items-center gap-2.5 px-2 py-2 rounded-md hover:bg-white/5 transition-colors">
              <Avatar className="w-7 h-7">
                <AvatarFallback className="bg-primary/20 text-primary text-xs font-semibold">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 text-left min-w-0">
                <p className="text-xs font-medium text-sidebar-foreground truncate">
                  {user?.userId || 'Unknown'}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {user?.role === 'admin' ? '管理员' : '用户'}
                </p>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="start" className="w-52">
            <div className="px-2 py-1.5">
              <p className="text-xs font-medium">{user?.userId}</p>
              <p className="text-xs text-muted-foreground mono">{user?.subjectId}</p>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-destructive focus:text-destructive" onClick={logout}>
              <LogOut className="w-3.5 h-3.5 mr-2" />
              退出登录
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  );
}

// ============================================================
// AppShell
// ============================================================

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="min-h-full p-6 page-enter">
          {children}
        </div>
      </main>
    </div>
  );
}

// ============================================================
// PublicShell - For login / invite pages
// ============================================================

export function PublicShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Minimal header */}
      <header className="h-14 border-b border-border flex items-center px-6">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-primary/20 flex items-center justify-center">
            <span className="text-primary font-bold text-xs" style={{ fontFamily: 'Space Grotesk' }}>CL</span>
          </div>
          <span className="font-semibold text-foreground" style={{ fontFamily: 'Space Grotesk' }}>
            ClawLoops
          </span>
        </div>
      </header>
      <main className="flex-1 flex items-center justify-center p-6">
        {children}
      </main>
    </div>
  );
}
