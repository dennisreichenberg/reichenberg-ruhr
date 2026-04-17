import type { Metadata } from "next";
import { PageHero } from "@/components/ui/PageHero";
import { ContactSection } from "@/components/sections/ContactSection";

export const metadata: Metadata = {
  title: "Kontakt & Buchung",
  description:
    "Nehmen Sie Kontakt auf oder buchen Sie direkt Ihr kostenloses Erstgespräch mit Dennis Reichenberg.",
};

export default function KontaktPage() {
  return (
    <>
      <PageHero
        title="Kontakt aufnehmen"
        subtitle="Ich freue mich auf Ihre Nachricht. Das erste Gespräch ist immer kostenlos und unverbindlich."
      />
      <ContactSection />
    </>
  );
}
