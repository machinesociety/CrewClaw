/**
 * Shared Page Components
 * Design: Crafted Dark - ClawLoops Platform
 *
 * PageHeader, EmptyState, ErrorDisplay, LoadingState, MonoText
 */

import { cn } from '@/lib/utils';
import { AlertCircle, RefreshCw, Inbox } from 'lucide-react';
import { Button } from '@/components/ui/button';

// ============================================================
// MonoText - Technical IDs and values
// ============================================================

export function MonoText({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={cn('mono text-xs text-muted-foreground', className)}>
      {children}
    </span>
  );
}

// ============================================================
// PageHeader
// ============================================================

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, actions, className }: PageHeaderProps) {
  return (
    <div className={cn('flex items-start justify-between mb-6', className)}>
      <div>
        <h1
          className="text-xl font-semibold text-foreground"
          style={{ fontFamily: 'Space Grotesk, system-ui' }}
        >
          {title}
        </h1>
        {description && (
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

// ============================================================
// SectionHeader
// ============================================================

export function SectionHeader({ title, className }: { title: string; className?: string }) {
  return (
    <h2
      className={cn('text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3', className)}
      style={{ fontFamily: 'Space Grotesk, system-ui' }}
    >
      {title}
    </h2>
  );
}

// ============================================================
// LoadingState - Skeleton rows
// ============================================================

export function LoadingRows({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="h-12 skeleton rounded-lg" />
      ))}
    </div>
  );
}

export function LoadingCard() {
  return (
    <div className="rounded-lg border border-border p-4 space-y-3">
      <div className="h-4 skeleton rounded w-1/3" />
      <div className="h-3 skeleton rounded w-2/3" />
      <div className="h-3 skeleton rounded w-1/2" />
    </div>
  );
}

// ============================================================
// EmptyState
// ============================================================

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}

export function EmptyState({ title, description, action, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-4">
        {icon || <Inbox className="w-6 h-6 text-muted-foreground" />}
      </div>
      <h3 className="text-sm font-medium text-foreground mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground max-w-xs">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

// ============================================================
// ErrorDisplay
// ============================================================

interface ErrorDisplayProps {
  code?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorDisplay({ code, message, onRetry, className }: ErrorDisplayProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
        <AlertCircle className="w-6 h-6 text-red-400" />
      </div>
      {code && (
        <span className="mono text-xs text-red-400/70 mb-1">{code}</span>
      )}
      <p className="text-sm text-muted-foreground max-w-xs">
        {message || '发生了一个错误'}
      </p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          className="mt-4 gap-2"
          onClick={onRetry}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          重试
        </Button>
      )}
    </div>
  );
}

// ============================================================
// InfoRow - Key-value display
// ============================================================

export function InfoRow({ label, value, mono }: { label: string; value?: React.ReactNode; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between py-2.5 border-b border-border/50 last:border-0">
      <span className="text-xs text-muted-foreground flex-shrink-0 w-32">{label}</span>
      <span className={cn('text-xs text-foreground text-right', mono && 'mono')}>
        {value ?? <span className="text-muted-foreground/50">—</span>}
      </span>
    </div>
  );
}

// ============================================================
// ConfirmDialog - Simple confirm wrapper
// ============================================================

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  destructive?: boolean;
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = '确认',
  cancelLabel = '取消',
  onConfirm,
  destructive,
}: ConfirmDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {description && (
            <AlertDialogDescription>{description}</AlertDialogDescription>
          )}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{cancelLabel}</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className={destructive ? 'bg-destructive hover:bg-destructive/90 text-destructive-foreground' : ''}
          >
            {confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
