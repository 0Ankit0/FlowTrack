'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  Bell,
  Settings,
  Building2,
  User,
  BriefcaseBusiness,
  FolderKanban,
  Ticket,
  ArrowRight,
  Rocket,
} from 'lucide-react';
import { OrgSwitcher } from './org-switcher';
import { useSystemCapabilities } from '@/hooks/use-system';
import { useAuthStore } from '@/store/auth-store';

const mainNavigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Tickets', href: '/tickets', icon: Ticket },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Releases', href: '/releases', icon: Rocket },
  { name: 'Workspace', href: '/tenants', icon: BriefcaseBusiness, feature: 'multitenancy' },
];

const supportNavigation = [
  { name: 'Profile', href: '/profile', icon: User },
  { name: 'Notifications', href: '/notifications', icon: Bell, feature: 'notifications' },
  { name: 'Organizations', href: '/tenants', icon: Building2, feature: 'multitenancy' },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: capabilities } = useSystemCapabilities();
  const user = useAuthStore((state) => state.user);
  const appName = process.env.NEXT_PUBLIC_APP_NAME ?? 'Flowtrack';

  const visibleNavigation = mainNavigation.filter(
    (item) => !item.feature || capabilities?.modules[item.feature] !== false
  );
  const visibleSupportNavigation = supportNavigation.filter(
    (item) => !item.feature || capabilities?.modules[item.feature] !== false
  );
  const showAdminSwitch = Boolean(user?.is_superuser);

  return (
    <aside className="fixed inset-y-0 left-0 z-10 w-72 border-r border-[rgba(15,23,42,0.08)] bg-[linear-gradient(180deg,#fffaf1_0%,#fffdf8_20%,#ffffff_100%)] shadow-[18px_0_80px_rgba(15,23,42,0.04)]">
      <div className="border-b border-[rgba(15,23,42,0.08)] px-5 py-5">
        <Link href="/dashboard" className="block">
          <div className="inline-flex items-center gap-3 rounded-full border border-[rgba(15,23,42,0.08)] bg-white px-4 py-2 shadow-[0_10px_30px_rgba(15,23,42,0.06)]">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[linear-gradient(135deg,#0f766e,#be185d)] text-[11px] font-black uppercase tracking-[0.18em] text-white">
              FT
            </span>
            <span className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-800">
              {appName}
            </span>
          </div>
        </Link>
        <p className="mt-4 text-xs uppercase tracking-[0.24em] text-slate-400">
          Delivery Control Room
        </p>
      </div>
      <OrgSwitcher />
      <nav className="flex flex-col gap-6 p-4 pt-0">
        <div>
          <div className="mb-2 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-400">
            Flowtrack
          </div>
          <div className="space-y-1">
            {visibleNavigation.map((item) => {
              const isActive =
                pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-[linear-gradient(135deg,rgba(15,118,110,0.14),rgba(190,24,93,0.12))] text-slate-900 shadow-[0_16px_40px_rgba(15,23,42,0.08)]'
                      : 'text-slate-600 hover:bg-[rgba(15,23,42,0.04)]'
                  }`}
                >
                  <item.icon className="h-4 w-4" />
                  {item.name}
                </Link>
              );
            })}
          </div>
        </div>

        <div>
          <div className="mb-2 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-400">
            Account
          </div>
          <div className="space-y-1">
            {visibleSupportNavigation.map((item) => {
              const isActive =
                pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-[rgba(15,23,42,0.05)] text-slate-900'
                      : 'text-slate-600 hover:bg-[rgba(15,23,42,0.04)]'
                  }`}
                >
                  <item.icon className="h-4 w-4" />
                  {item.name}
                </Link>
              );
            })}
          </div>
        </div>
        {showAdminSwitch ? (
          <div className="mt-auto border-t border-[rgba(15,23,42,0.08)] pt-4">
            <Link
              href="/admin/dashboard"
              className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-slate-600 transition-colors hover:bg-[rgba(15,23,42,0.04)]"
            >
              <ArrowRight className="h-4 w-4" />
              Open Admin Panel
            </Link>
          </div>
        ) : null}
      </nav>
    </aside>
  );
}
