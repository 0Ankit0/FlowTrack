'use client';

import { useEffect, useState } from 'react';
import { SignupForm } from '@/components/auth/signup-form';
import { getEnabledProviders, type OAuthProvider } from '@/lib/oauth';

export default function SignupPage() {
  const [enabledProviders, setEnabledProviders] = useState<OAuthProvider[]>([]);

  useEffect(() => {
    void getEnabledProviders().then(setEnabledProviders);
  }, []);

  return <SignupForm enabledProviders={enabledProviders} />;
}
