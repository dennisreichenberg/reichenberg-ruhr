import type { Metadata } from "next";
import { HeroSection } from "@/components/sections/HeroSection";
import { TrustBar } from "@/components/sections/TrustBar";
import { ServicesTeaser } from "@/components/sections/ServicesTeaser";
import { AboutTeaser } from "@/components/sections/AboutTeaser";
import { TestimonialsSection } from "@/components/sections/TestimonialsSection";
import { CTABanner } from "@/components/sections/CTABanner";

export const metadata: Metadata = {
  title: "Dennis Reichenberg – Berufliche Beratung & Karriere-Coaching",
  description:
    "Professionelle Karriereberatung mit Dennis Reichenberg. Von der Gehaltsverhandlung bis zur strategischen Karriereplanung – ich begleite Sie auf Ihrem Weg.",
};

export default function HomePage() {
  return (
    <>
      <HeroSection />
      <TrustBar />
      <ServicesTeaser />
      <AboutTeaser />
      <TestimonialsSection />
      <CTABanner />
    </>
  );
}
