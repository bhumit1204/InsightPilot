import type { Metadata } from "next";
import "@fontsource-variable/atkinson-hyperlegible-next";
import "./globals.css";

export const metadata: Metadata = {
  title: "InsightPilot",
  description: "Upload a CSV and see what is in your data, what changed, and why.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col">{children}</body>
    </html>
  );
}