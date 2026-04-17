"use client";

import { motion } from "framer-motion";
import { SectionHeader } from "@/components/ui/SectionHeader";

const values = [
  {
    icon: "🎯",
    title: "Klarheit",
    description:
      "Keine leeren Versprechen. Ich sage Ihnen ehrlich, was realistisch ist – und wie Sie es erreichen.",
  },
  {
    icon: "🤝",
    title: "Augenhöhe",
    description:
      "Ich begegne jedem Klienten respektvoll und auf Augenhöhe. Ihre Situation ist einmalig – meine Beratung auch.",
  },
  {
    icon: "📊",
    title: "Ergebnisorientierung",
    description:
      "Mein Erfolg ist Ihr Erfolg. Ich arbeite so lange, bis wir gemeinsam ein konkretes, messbares Ergebnis erreicht haben.",
  },
  {
    icon: "🔒",
    title: "Diskretion",
    description:
      "Was wir besprechen, bleibt zwischen uns. Absolute Vertraulichkeit ist für mich selbstverständlich.",
  },
];

export function ValuesSection() {
  return (
    <section className="py-20 lg:py-28 bg-surface">
      <div className="container-site">
        <SectionHeader
          eyebrow="Was mich antreibt"
          title="Meine Kernwerte"
          subtitle="Diese Werte leiten meine Arbeit und mein Verhältnis zu Ihnen."
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {values.map((value, i) => (
            <motion.div
              key={value.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="text-center p-6 rounded-card border border-border hover:border-gold/30 transition-colors"
            >
              <div className="text-4xl mb-4">{value.icon}</div>
              <h3 className="font-serif text-lg font-bold text-navy mb-3">
                {value.title}
              </h3>
              <p className="font-sans text-sm text-text-secondary leading-relaxed">
                {value.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
