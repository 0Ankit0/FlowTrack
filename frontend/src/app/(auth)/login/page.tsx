'use client';

import { useEffect, useState } from 'react';
import { LoginForm } from '@/components/auth/login-form';
import { getEnabledProviders, type OAuthProvider } from '@/lib/oauth';

export default function LoginPage() {
  const [enabledProviders, setEnabledProviders] = useState<OAuthProvider[]>([]);

  useEffect(() => {
    void getEnabledProviders().then(setEnabledProviders);
  }, []);

  return <LoginForm enabledProviders={enabledProviders} />;
}
