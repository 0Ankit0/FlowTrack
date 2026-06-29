import { useEffect } from 'react';
import { Navigate, Outlet, Route, Routes } from 'react-router-dom';
import { Providers } from '@/components/providers';
import { THEME_PRESETS } from '@/lib/themes';
import HomePage from '@/app/page';
import AuthLayout from '@/app/(auth)/layout';
import LoginPage from '@/app/(auth)/login/page';
import SignupPage from '@/app/(auth)/signup/page';
import ForgotPasswordPage from '@/app/(auth)/forgot-password/page';
import ResetPasswordPage from '@/app/(auth)/reset-password/page';
import VerifyEmailPage from '@/app/(auth)/verify-email/page';
import OtpVerifyPage from '@/app/(auth)/otp-verify/page';
import AcceptInvitationPage from '@/app/(auth)/accept-invitation/page';
import AuthCallbackPage from '@/app/(auth)/auth-callback/page';
import PaymentCallbackPage from '@/app/(auth)/payment-callback/page';
import UserDashboardLayout from '@/app/(user-dashboard)/layout';
import DashboardPage from '@/app/(user-dashboard)/dashboard/page';
import TicketsPage from '@/app/(user-dashboard)/tickets/page';
import ProjectsPage from '@/app/(user-dashboard)/projects/page';
import ReleasesPage from '@/app/(user-dashboard)/releases/page';
import TenantsPage from '@/app/(user-dashboard)/tenants/page';
import NotificationsPage from '@/app/(user-dashboard)/notifications/page';
import SettingsPage from '@/app/(user-dashboard)/settings/page';
import ProfilePage from '@/app/(user-dashboard)/profile/page';
import RbacPage from '@/app/(user-dashboard)/rbac/page';
import UserRolePage from '@/app/(user-dashboard)/rbac/[roleId]/page';
import TokensPage from '@/app/(user-dashboard)/tokens/page';
import FinancesPage from '@/app/(user-dashboard)/finances/page';
import MapsPage from '@/app/(user-dashboard)/maps/page';
import AdminDashboardLayout from '@/app/(admin-dashboard)/layout';
import AdminDashboardPage from '@/app/(admin-dashboard)/admin/dashboard/page';
import AdminUsersPage from '@/app/(admin-dashboard)/admin/users/page';
import AdminRbacPage from '@/app/(admin-dashboard)/admin/rbac/page';
import AdminRolePage from '@/app/(admin-dashboard)/admin/rbac/[roleId]/page';
import AdminSecurityReviewPage from '@/app/(admin-dashboard)/admin/security-review/page';
// import AdminLogsPage from '@/app/(admin-dashboard)/admin/logs/page';

function ThemeBootstrap() {
  useEffect(() => {
    try {
      const presets = THEME_PRESETS;
      const storedTheme = localStorage.getItem('theme-storage');
      let activeThemeId = presets[0].id;
      let customThemes: Array<(typeof THEME_PRESETS)[number]> = [];

      if (storedTheme) {
        const parsed = JSON.parse(storedTheme) as {
          state?: { activeThemeId?: string; customThemes?: Array<(typeof THEME_PRESETS)[number]> };
        };
        if (parsed?.state?.activeThemeId) {
          activeThemeId = parsed.state.activeThemeId;
        }
        if (Array.isArray(parsed?.state?.customThemes)) {
          customThemes = parsed.state.customThemes;
        }
      }

      const themes = presets.concat(customThemes);
      const activeTheme = themes.find((theme) => theme.id === activeThemeId) ?? presets[0];
      const root = document.documentElement;
      root.dataset.themeId = activeTheme.id;
      root.dataset.themeMode = activeTheme.mode;
      root.style.colorScheme = activeTheme.mode;
      Object.entries(activeTheme.palette).forEach(([key, value]) => {
        const cssName = key.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`);
        root.style.setProperty(`--${cssName}`, value);
      });
    } catch {
      document.documentElement.dataset.themeMode = 'light';
    }
  }, []);

  return null;
}

function RootLayout() {
  return (
    <Providers>
      <ThemeBootstrap />
      <Outlet />
    </Providers>
  );
}

function AuthShell() {
  return (
    <AuthLayout>
      <Outlet />
    </AuthLayout>
  );
}

function UserShell() {
  return (
    <UserDashboardLayout>
      <Outlet />
    </UserDashboardLayout>
  );
}

function AdminShell() {
  return (
    <AdminDashboardLayout>
      <Outlet />
    </AdminDashboardLayout>
  );
}

export function App() {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        <Route path="/" element={<HomePage />} />

        <Route element={<AuthShell />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          <Route path="/otp-verify" element={<OtpVerifyPage />} />
          <Route path="/accept-invitation" element={<AcceptInvitationPage />} />
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
          <Route path="/payment-callback" element={<PaymentCallbackPage />} />
        </Route>

        <Route element={<UserShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/tickets" element={<TicketsPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/releases" element={<ReleasesPage />} />
          <Route path="/tenants" element={<TenantsPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/rbac" element={<RbacPage />} />
          <Route path="/rbac/:roleId" element={<UserRolePage />} />
          <Route path="/tokens" element={<TokensPage />} />
          <Route path="/finances" element={<FinancesPage />} />
          <Route path="/maps" element={<MapsPage />} />
        </Route>

        <Route element={<AdminShell />}>
          <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/rbac" element={<AdminRbacPage />} />
          <Route path="/admin/rbac/:roleId" element={<AdminRolePage />} />
          <Route path="/admin/security-review" element={<AdminSecurityReviewPage />} />
          {/* <Route path="/admin/logs" element={<AdminLogsPage />} /> */}
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
