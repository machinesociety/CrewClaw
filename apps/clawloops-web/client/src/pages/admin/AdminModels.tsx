/**
 * Admin Models Page - /admin/models
 * Design: Crafted Dark - ClawLoops Platform
 *
 * Per 页面调用流程_BFF编排.md §6.4
 * List models, toggle enabled/visible, set default
 */

import { useCallback, useEffect, useState } from 'react';
import { adminApi, Model, isAppError } from '@/lib/api';
import { RequireAdmin } from '@/components/guards/RouteGuard';
import { AppShell } from '@/components/layout/AppShell';
import { StatusBadge } from '@/components/shared/StatusBadge';
import {
  PageHeader,
  LoadingRows,
  ErrorDisplay,
  EmptyState,
  MonoText,
} from '@/components/shared/PageComponents';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import { RefreshCw, Cpu, Star } from 'lucide-react';

// ============================================================
// Main Page
// ============================================================

function AdminModelsContent() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const loadModels = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminApi.models.list();
      setModels(res.models || []);
    } catch (e) {
      setError(isAppError(e) ? e.message : '加载模型列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const handleUpdate = async (modelId: string, patch: Partial<Model>) => {
    setUpdatingId(modelId);
    try {
      const updated = await adminApi.models.update(modelId, patch);
      setModels((prev) =>
        prev.map((m) => (m.modelId === modelId ? { ...m, ...updated } : m))
      );
      toast.success('模型配置已更新');
    } catch (e) {
      toast.error(isAppError(e) ? e.message : '更新失败');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleSetDefault = async (modelId: string) => {
    setUpdatingId(modelId);
    try {
      await adminApi.models.update(modelId, { isDefault: true });
      // Refresh to get updated state
      await loadModels();
      toast.success('默认模型已更新');
    } catch (e) {
      toast.error(isAppError(e) ? e.message : '设置默认失败');
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="page-enter">
      <PageHeader
        title="模型治理"
        description="管理平台可用 AI 模型"
        actions={
          <Button variant="outline" size="sm" className="gap-2" onClick={loadModels} disabled={loading}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        }
      />

      <Card className="card-glow">
        <CardContent className="p-0">
          {loading && (
            <div className="p-4">
              <LoadingRows count={4} />
            </div>
          )}

          {!loading && error && (
            <ErrorDisplay message={error} onRetry={loadModels} className="py-8" />
          )}

          {!loading && !error && models.length === 0 && (
            <EmptyState
              title="暂无模型"
              description="尚未配置任何 AI 模型"
              icon={<Cpu className="w-6 h-6 text-muted-foreground" />}
            />
          )}

          {!loading && !error && models.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>模型 ID</TableHead>
                  <TableHead>名称</TableHead>
                  <TableHead>Provider</TableHead>
                  <TableHead>默认</TableHead>
                  <TableHead>启用</TableHead>
                  <TableHead>可见</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {models.map((model) => (
                  <TableRow key={model.modelId}>
                    <TableCell>
                      <MonoText>{model.modelId}</MonoText>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm font-medium text-foreground">{model.name}</span>
                    </TableCell>
                    <TableCell>
                      <span className="text-xs text-muted-foreground">{model.provider || '—'}</span>
                    </TableCell>
                    <TableCell>
                      {model.isDefault ? (
                        <StatusBadge variant="info">
                          <Star className="w-3 h-3 mr-1 inline" />
                          默认
                        </StatusBadge>
                      ) : (
                        <span className="text-muted-foreground/40 text-xs">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={model.enabled ?? false}
                        disabled={updatingId === model.modelId}
                        onCheckedChange={(checked) =>
                          handleUpdate(model.modelId, { enabled: checked })
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={model.userVisible ?? false}
                        disabled={updatingId === model.modelId}
                        onCheckedChange={(checked) =>
                          handleUpdate(model.modelId, { userVisible: checked })
                        }
                      />
                    </TableCell>
                    <TableCell className="text-right">
                      {!model.isDefault && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-xs gap-1"
                          disabled={updatingId === model.modelId}
                          onClick={() => handleSetDefault(model.modelId)}
                        >
                          <Star className="w-3 h-3" />
                          设为默认
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function AdminModelsPage() {
  return (
    <RequireAdmin>
      <AppShell>
        <AdminModelsContent />
      </AppShell>
    </RequireAdmin>
  );
}
