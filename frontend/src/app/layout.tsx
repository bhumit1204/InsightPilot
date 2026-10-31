import type { Metadata } from "next";
import "@fontsource-variable/atkinson-hyperlegible-next";
import "./globals.css";

import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { themeScript } from "@/lib/theme";

import { Providers } from "./providers";

export const metadata: Metadata = {
  title: { default: "InsightPilot", template: "%s | InsightPilot" },
  description: "Upload a CSV and see what is in your data, what changed, and why.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // suppressHydrationWarning: the theme script may set data-theme before React loads.
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="flex min-h-full flex-col">
        <Providers>
          <SiteHeader />
          <div className="flex flex-1 flex-col">{children}</div>
          <SiteFooter />
        </Providers>
      </body>
    </html>
  );
}
