"use client";

import { motion } from "framer-motion";
import { SectionHeader } from "@/components/ui/SectionHeader";

const steps = [
  {
    number: "01",
    title: "Erstgespräch",
    description:
      "Kostenlos und unverbindlich. Wir besprechen Ihre aktuelle Situation, Ihre Ziele und schauen, ob wir gut zusammenpassen.",
  },
  {
    number: "02",
    title: "Analyse & Strategie",
    description:
      "Ich analysiere Ihren individuellen Fall und entwickle einen maßgeschneiderten Plan für Ihre Situation und Ziele.",
  },
  {
    number: "03",
    title: "Umsetzung",
    description:
      "Gemeinsam setzen wir die Strategie um – mit konkreten Materialien, Übungen und regelmäßigem Feedback.",
  },
  {
    number: "04",
    title: "Ergebnis & Nachbetreuung",
    description:
      "Nach Ihrem Erfolg bleibe ich als Ansprechpartner für Folgefragen und weitere Karriereschritte an Ihrer Seite.",
  },
];

export function ProcessSection() {
  return (
    <section className="py-20 lg:py-28 bg-surface">
      <div className="container-site">
        <SectionHeader
          eyebrow="Mein Vorgehen"
          title="So arbeiten wir zusammen"
          subtitle="Ein strukturierter Prozess für maximalen Erfolg."
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, i) => (
            <motion.div
              key={step.number}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="relative"
            >
              {/* Connector line */}
              {i < steps.length - 1 && (
                <div className="hidden lg:block absolute top-6 left-full w-full h-px bg-border -translate-x-4 z-0" />
              )}
              <div className="relative z-10">
                <div className="w-12 h-12 rounded-full bg-navy flex items-center justify-center mb-4">
                  <span className="font-serif text-sm font-bold text-gold">
                    {step.number}
                  </span>
                </div>
                <h3 className="font-serif text-lg font-bold text-navy mb-2">
                  {step.title}
                </h3>
                <p className="font-sans text-sm text-text-secondary leading-relaxed">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
