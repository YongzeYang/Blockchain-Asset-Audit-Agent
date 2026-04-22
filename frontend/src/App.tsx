import { Routes, Route, Navigate } from 'react-router-dom';
import AppShell from '@/components/AppShell';
import DashboardPage from '@/pages/DashboardPage';
import SkillsPage from '@/pages/SkillsPage';
import SkillDetailPage from '@/pages/SkillDetailPage';
import SkillGeneratorPage from '@/pages/SkillGeneratorPage';
import AuditNewPage from '@/pages/AuditNewPage';
import RunsPage from '@/pages/RunsPage';
import RunDetailPage from '@/pages/RunDetailPage';

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/skills" element={<SkillsPage />} />
        <Route path="/skills/new" element={<SkillGeneratorPage />} />
        <Route path="/skills/:id" element={<SkillDetailPage />} />
        <Route path="/audit/new" element={<AuditNewPage />} />
        <Route path="/runs" element={<RunsPage />} />
        <Route path="/runs/:runId" element={<RunDetailPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
