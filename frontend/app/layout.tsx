import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Airport Wayfinding Assistant",
  description:
    "Multilingual voice/text airport wayfinding assistant (Arabic/Darija/French/English).",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
