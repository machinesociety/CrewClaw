import { AppShell } from '@/components/layout/AppShell';
import { RequireAdmin } from '@/components/guards/RouteGuard';
import { PublicAreaView } from '../PublicArea';

export default function AdminPublicAreaPage() {
  return (
    <RequireAdmin>
      <AppShell>
        <PublicAreaView mode="admin" basePath="/admin/public-area" />
      </AppShell>
    </RequireAdmin>
  );
}
