"use client";

import { motion } from "framer-motion";
import { SectionHeader } from "@/components/ui/SectionHeader";

const testimonials = [
  {
    quote:
      "Dennis hat mir geholfen, mein Gehalt um 20% zu erhöhen. Seine Strategie und die konkreten Formulierungen waren absolut wertvoll. Ich hätte das ohne seine Unterstützung nie gewagt.",
    name: "Markus T.",
    role: "Senior Software Engineer",
  },
  {
    quote:
      "Nach Jahren im gleichen Job wusste ich nicht, wie ich weitermachen soll. Dennis hat mir geholfen, meine Stärken zu erkennen und einen klaren Karriereweg zu entwickeln.",
    name: "Laura K.",
    role: "Projektleiterin, Maschinenbau",
  },
  {
    quote:
      "Das Interview-Training war Gold wert. Ich war bestens vorbereitet und habe die Stelle bekommen. Klare Empfehlung für alle, die ihren nächsten Schritt machen wollen.",
    name: "Stefan R.",
    role: "IT-Consultant",
  },
];

export function TestimonialsSection() {
  return (
    <section className="bg-navy py-20 lg:py-28">
      <div className="container-site">
        <SectionHeader
          eyebrow="Stimmen meiner Klienten"
          title="Was andere sagen"
          subtitle="Echte Ergebnisse von echten Menschen."
          centered
          light
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          {testimonials.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.12, duration: 0.5 }}
              className="bg-white/5 border border-white/10 rounded-card p-6 lg:p-8"
            >
              <p className="text-gold text-3xl mb-4 font-serif leading-none">"</p>
              <p className="font-sans text-body-md text-white/80 leading-relaxed mb-6 italic">
                {t.quote}
              </p>
              <div>
                <p className="font-sans font-semibold text-white text-sm">{t.name}</p>
                <p className="font-sans text-xs text-white/50">{t.role}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
