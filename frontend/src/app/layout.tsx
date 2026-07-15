import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SupportForge",
  description: "企业级 SaaS 智能客服 AI 平台",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
