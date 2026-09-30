import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sura Raksha",
  description: "Cyclone Impact Forecaster",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}