import type { Metadata } from 'next';
import { AppProvider } from '../lib/context';
import AppShell from '../components/AppShell';
import './globals.css';

export const metadata: Metadata = {
  title: 'ProcedureGuard — Enterprise Quality Evidence Console',
  description: 'Microsoft Fluent/Azure quality assurance verification console for manufacturing compliance reports.',
  icons: {
    icon: '/favicon.ico',
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full select-none">
      <body className="h-full antialiased font-sans bg-pg-app-background text-pg-ink flex flex-col">
        <AppProvider>
          <AppShell>
            {children}
          </AppShell>
        </AppProvider>
      </body>
    </html>
  );
}
