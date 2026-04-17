import type { Metadata } from "next";
import { PageHero } from "@/components/ui/PageHero";
import { ServicesGrid } from "@/components/sections/ServicesGrid";
import { ProcessSection } from "@/components/sections/ProcessSection";
import { FAQSection } from "@/components/sections/FAQSection";
import { CTABanner } from "@/components/sections/CTABanner";

export const metadata: Metadata = {
  title: "Leistungen",
  description:
    "Karriereberatung, Gehaltsverhandlung, Bewerbungscoaching und mehr. Entdecken Sie das vollständige Beratungsangebot von Dennis Reichenberg.",
};

export default function LeistungenPage() {
  return (
    <>
      <PageHero
        title="Leistungen"
        subtitle="Maßgeschneiderte Beratung für Ihren beruflichen Erfolg – von der ersten Analyse bis zum finalen Ergebnis."
      />
      <ServicesGrid />
      <ProcessSection />
      <FAQSection />
      <CTABanner />
    </>
  );
}
