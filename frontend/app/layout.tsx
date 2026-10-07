import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "零售金融数字人客服",
  description: "账户、转账、卡片、密码、信用卡、理财说明书、网点与投诉咨询",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
