// app/layout.tsx
import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '檢修系統 - 裂縫分析',
  description: '混凝土裂縫檢修與分析系統',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-TW">
      <body>{children}</body>
    </html>
  );
}