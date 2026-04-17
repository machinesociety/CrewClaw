import { useCallback, useEffect, useState } from 'react';
import { adminApi, Model, isAppError } from '@/lib/api';
import { RequireAdmin } from '@/components/guards/RouteGuard';
import { AppShell } from '@/components/layout/AppShell';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { PageHeader, LoadingRows, ErrorDisplay, EmptyState, MonoText } from '@/components/shared/PageComponents';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from 'sonner';
import { RefreshCw, Cpu, Star } from 'lucide-react';

function AdminModelsContent() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

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

  const showRuntimeRefreshHint = useCallback((updated: Partial<Model>) => {
    if (!updated.runtimeRefreshTriggered) return;
    toast.success('模型配置已更新，OpenClaw 已刷新', {
      description: updated.runtimeBrowserUrl
        ? `当前工作区模型目录已重载。如聊天页已打开，请刷新一次页面：${updated.runtimeBrowserUrl}`
        : '当前工作区模型目录已重载。如聊天页已打开，请刷新一次页面。',
    });
  }, []);

  const handleUpdate = async (modelId: string, patch: Partial<Model>) => {
    setUpdatingId(modelId);
    try {
      const updated = await adminApi.models.update(modelId, patch);
      setModels((prev) => prev.map((m) => (m.modelId === modelId ? { ...m, ...updated } : m)));
      if (updated.runtimeRefreshTriggered) {
        showRuntimeRefreshHint(updated);
      } else {
        toast.success('模型配置已更新');
      }
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
      await loadModels();
      toast.success('默认模型已更新');
    } catch (e) {
      toast.error(isAppError(e) ? e.message : '设置默认失败');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleSyncOpenRouter = async () => {
    setSyncing(true);
    try {
      const res = await adminApi.models.syncOpenRouter();
      await loadModels();
      toast.success('OpenRouter 模型同步完成', {
        description: `拉取 ${res.fetched}，新增 ${res.created}，更新 ${res.updated}`,
      });
    } catch (e) {
      toast.error(isAppError(e) ? e.message : '同步失败');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="page-enter">
      <PageHeader
        title="模型治理"
        description="管理平台可用 AI 模型"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2" onClick={handleSyncOpenRouter} disabled={loading || syncing}>
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
              同步 OpenRouter
            </Button>
            <Button variant="outline" size="sm" className="gap-2" onClick={loadModels} disabled={loading || syncing}>
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
          </div>
        }
      />

      <Card className="card-glow">
        <CardContent className="p-0">
          {loading && (
            <div className="p-4">
              <LoadingRows count={4} />
            </div>
          )}

          {!loading && error && <ErrorDisplay message={error} onRetry={loadModels} className="py-8" />}

          {!loading && !error && models.length === 0 && (
            <EmptyState title="暂无模型" description="尚未配置任何 AI 模型" icon={<Cpu className="w-6 h-6 text-muted-foreground" />} />
          )}

          {!loading && !error && models.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>模型 ID</TableHead>
                  <TableHead>名称</TableHead>
                  <TableHead>Provider</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>默认</TableHead>
                  <TableHead>启用</TableHead>
                  <TableHead>可见</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {models.map((model) => (
                  <TableRow key={model.modelId}>
                    <TableCell><MonoText>{model.modelId}</MonoText></TableCell>
                    <TableCell><span className="text-sm font-medium text-foreground">{model.name}</span></TableCell>
                    <TableCell><span className="text-xs text-muted-foreground">{model.provider || '—'}</span></TableCell>
                    <TableCell>
                      <Select
                        value={model.pricingType || 'free'}
                        onValueChange={(v) => handleUpdate(model.modelId, { pricingType: v as Model['pricingType'] })}
                        disabled={updatingId === model.modelId}
                      >
                        <SelectTrigger size="sm" className="min-w-[92px]">
                          <SelectValue placeholder="选择类型" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="free">免费</SelectItem>
                          <SelectItem value="paid">付费</SelectItem>
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      {model.isDefault ? (
                        <StatusBadge variant="info">
                          <Star className="w-3 h-3 mr-1 inline" />默认
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
                          handleUpdate(
                            model.modelId,
                            checked ? { enabled: true, userVisible: true, visible: true } : { enabled: false }
                          )
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={(model.userVisible ?? model.visible) ?? false}
                        disabled={updatingId === model.modelId}
                        onCheckedChange={(checked) => handleUpdate(model.modelId, { userVisible: checked, visible: checked })}
                      />
                    </TableCell>
                    <TableCell className="text-right">
                      {!model.isDefault && (
                        <Button variant="ghost" size="sm" className="h-7 text-xs gap-1" disabled={updatingId === model.modelId} onClick={() => handleSetDefault(model.modelId)}>
                          <Star className="w-3 h-3" />设为默认
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
