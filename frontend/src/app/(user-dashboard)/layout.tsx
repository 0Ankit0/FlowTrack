'use client';

import { ProtectedRoute } from '@/components/auth/protected-route';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';

export default function UserDashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(251,191,36,0.08),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(20,184,166,0.08),transparent_24%),linear-gradient(180deg,#fff9ef_0%,#fffdf8_32%,#f8fafc_100%)]">
        <Sidebar />
        <Header />
        <main className="ml-72 min-h-screen pt-20 p-8">{children}</main>
      </div>
    </ProtectedRoute>
  );
}
