"use client";

import { motion } from "framer-motion";
import { ServiceCard } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { LinkButton } from "@/components/ui/Button";

const services = [
  {
    icon: "💼",
    title: "Gehaltsverhandlung",
    description:
      "Fundierte Strategien und konkrete Argumente für Ihre nächste Gehaltsverhandlung – egal ob beim aktuellen oder neuen Arbeitgeber.",
    bullets: ["Marktgerechte Einschätzung", "Verhandlungsstrategie", "Argumente & Formulierungen"],
  },
  {
    icon: "🎯",
    title: "Karriereplanung",
    description:
      "Gemeinsam entwickeln wir eine klare Vision für Ihre berufliche Zukunft und definieren konkrete Schritte zur Zielerreichung.",
    bullets: ["Potenzialanalyse", "Zielentwicklung", "Roadmap & Meilensteine"],
  },
  {
    icon: "📋",
    title: "Bewerbungscoaching",
    description:
      "Von der Bewerbungsunterlagen-Optimierung bis zur Interview-Vorbereitung – ich bereite Sie optimal auf Ihren nächsten Karriereschritt vor.",
    bullets: ["CV & Anschreiben", "LinkedIn-Optimierung", "Interview-Training"],
  },
];

export function ServicesTeaser() {
  return (
    <section className="py-20 lg:py-28 bg-background">
      <div className="container-site">
        <SectionHeader
          eyebrow="Meine Leistungen"
          title="Wie ich Sie unterstütze"
          subtitle="Individuelle Beratung auf Augenhöhe – für Ihren nächsten beruflichen Durchbruch."
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {services.map((service, i) => (
            <motion.div
              key={service.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.12, duration: 0.5 }}
            >
              <ServiceCard
                icon={<span>{service.icon}</span>}
                title={service.title}
                description={service.description}
                bullets={service.bullets}
              />
            </motion.div>
          ))}
        </div>

        <div className="mt-10 flex justify-center">
          <LinkButton href="/leistungen" variant="secondary">
            Alle Leistungen ansehen
          </LinkButton>
        </div>
      </div>
    </section>
  );
}
