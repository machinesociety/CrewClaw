/**
 * StatusBadge - Semantic status indicator
 * Design: Crafted Dark - ClawLoops Platform
 */

import { cn } from '@/lib/utils';

type StatusVariant = 'success' | 'warning' | 'error' | 'info' | 'neutral' | 'pending';

interface StatusBadgeProps {
  variant: StatusVariant;
  children: React.ReactNode;
  className?: string;
  dot?: boolean;
}

const variantStyles: Record<StatusVariant, string> = {
  success: 'bg-green-500/15 text-green-400 border border-green-500/20',
  warning: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/20',
  error: 'bg-red-500/15 text-red-400 border border-red-500/20',
  info: 'bg-blue-500/15 text-blue-400 border border-blue-500/20',
  neutral: 'bg-white/5 text-white/50 border border-white/10',
  pending: 'bg-orange-500/15 text-orange-400 border border-orange-500/20',
};

const dotStyles: Record<StatusVariant, string> = {
  success: 'bg-green-400',
  warning: 'bg-yellow-400',
  error: 'bg-red-400',
  info: 'bg-blue-400',
  neutral: 'bg-white/40',
  pending: 'bg-orange-400',
};

export function StatusBadge({ variant, children, className, dot }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium',
        variantStyles[variant],
        className
      )}
    >
      {dot && (
        <span className={cn('w-1.5 h-1.5 rounded-full pulse-dot', dotStyles[variant])} />
      )}
      {children}
    </span>
  );
}

// Map runtime observedState to badge variant
export function runtimeStateVariant(state?: string): StatusVariant {
  switch (state) {
    case 'running': return 'success';
    case 'creating': return 'info';
    case 'stopped': return 'neutral';
    case 'error': return 'error';
    case 'deleted': return 'neutral';
    default: return 'neutral';
  }
}

// Map invitation status to badge variant
export function invitationStatusVariant(status?: string): StatusVariant {
  switch (status) {
    case 'pending': return 'pending';
    case 'consumed': return 'success';
    case 'revoked': return 'error';
    default: return 'neutral';
  }
}

// Map user status to badge variant
export function userStatusVariant(status?: string): StatusVariant {
  switch (status) {
    case 'active': return 'success';
    case 'disabled': return 'error';
    default: return 'neutral';
  }
}

// Map task status to badge variant
export function taskStatusVariant(status?: string): StatusVariant {
  switch (status) {
    case 'succeeded': return 'success';
    case 'running': return 'info';
    case 'pending': return 'pending';
    case 'failed': return 'error';
    case 'canceled': return 'neutral';
    default: return 'neutral';
  }
}
