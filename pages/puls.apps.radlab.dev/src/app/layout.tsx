import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Puls Informacji — RadLab",
  description:
    "Co słychać teraz? Wybierz temat i zbierz aktualne wiadomości z wielu źródeł w jeden czytelny artykuł z Pulsem Informacji by RadLab.",
  icons: {
    icon: "/logo-circle.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pl">
      <body className="min-h-screen bg-paper-100 text-ink-700 antialiased">
        {children}
      </body>
    </html>
  );
}
