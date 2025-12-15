import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Football Match Predictions | AI-Powered Match Analysis",
  description:
    "Get AI-powered predictions for football matches across Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Champions League, and World Cup. Advanced analytics and insights.",
  openGraph: {
    title: "Football Match Predictions | AI-Powered Match Analysis",
    description:
      "Get AI-powered predictions for football matches across Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Champions League, and World Cup. Advanced analytics and insights.",
    url: "https://football.ketankarki.wiki",
    siteName: "Football Match Predictions",
    images: [
      {
        url: "https://football.ketankarki.wiki/og-image.png",
        width: 1200,
        height: 630,
        alt: "Football Match Predictions - AI-Powered Analysis",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Football Match Predictions | AI-Powered Match Analysis",
    description:
      "Get AI-powered predictions for football matches across Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Champions League, and World Cup.",
    images: ["https://football.ketankarki.wiki/og-image.png"],
  },
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
