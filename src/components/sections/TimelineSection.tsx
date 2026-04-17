"use client";

import { motion } from "framer-motion";
import { SectionHeader } from "@/components/ui/SectionHeader";

const timeline = [
  {
    year: "2023",
    title: "Softwareentwickler @ VU SOLUTIONS",
    description:
      "Einstieg bei VU SOLUTIONS als Softwareentwickler mit einem Jahresgehalt von 70.000 €. Schwerpunkt auf Softwareentwicklung und digitale Transformation.",
  },
  {
    year: "2024",
    title: "Head of AI @ VU SOLUTIONS",
    description:
      "Beförderung zum Head of AI. Verantwortung für die Integration von KI in Unternehmensprodukte und die Optimierung von Arbeitsprozessen durch KI-Agenten.",
  },
  {
    year: "2025",
    title: "Start der Karriereberatung",
    description:
      "Launch der eigenen Beratungstätigkeit. Fokus auf Karriereberatung, Gehaltsverhandlung und Tech-Karriere-Coaching.",
  },
  {
    year: "2026",
    title: "Erweiterung des Angebots",
    description:
      "Ausbau der Beratungsleistungen auf Führungskräfte-Entwicklung und berufliche Neuorientierung im Tech-Bereich.",
  },
];

export function TimelineSection() {
  return (
    <section className="py-20 lg:py-28 bg-background">
      <div className="container-site">
        <SectionHeader
          eyebrow="Mein Werdegang"
          title="Stationen & Erfahrungen"
          subtitle="Ein Überblick über meinen beruflichen Weg."
        />

        <div className="relative max-w-3xl">
          {/* Vertical line */}
          <div className="absolute left-6 top-0 bottom-0 w-px bg-border" />

          <div className="space-y-10">
            {timeline.map((item, i) => (
              <motion.div
                key={item.year}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
                className="relative pl-16"
              >
                {/* Dot */}
                <div className="absolute left-4 top-1 w-4 h-4 rounded-full bg-gold border-4 border-background -translate-x-1/2 z-10" />

                <div className="card p-5 lg:p-6">
                  <p className="font-sans text-xs font-semibold text-gold mb-1">
                    {item.year}
                  </p>
                  <h3 className="font-serif text-lg font-bold text-navy mb-2">
                    {item.title}
                  </h3>
                  <p className="font-sans text-sm text-text-secondary leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
