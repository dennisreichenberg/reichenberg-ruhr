import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Dennis Reichenberg – Berufliche Beratung & Karriere-Coaching",
    template: "%s | Dennis Reichenberg",
  },
  description:
    "Professionelle Karriereberatung für Fach- und Führungskräfte. Gehaltsverhandlung, Karriereplanung und Bewerbungscoaching mit Dennis Reichenberg.",
  keywords: [
    "Karriereberatung",
    "Berufliche Beratung",
    "Gehaltsverhandlung",
    "Bewerbungscoaching",
    "Career Coaching",
    "Dennis Reichenberg",
  ],
  openGraph: {
    type: "website",
    locale: "de_DE",
    siteName: "Dennis Reichenberg – Berufliche Beratung",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de" className={`${inter.variable} ${playfair.variable}`}>
      <body className="antialiased">
        <Header />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
