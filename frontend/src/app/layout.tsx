import { Providers } from '@/components/providers';
import './globals.css';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <Providers>
      <div className="antialiased">{children}</div>
    </Providers>
  );
}
