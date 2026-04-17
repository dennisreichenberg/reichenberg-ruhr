"use client";

import { motion } from "framer-motion";

export function StorySection() {
  return (
    <section className="py-20 lg:py-28 bg-surface">
      <div className="container-site">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-start">
          {/* Photo */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="sticky top-28"
          >
            <div className="aspect-[4/5] rounded-card bg-background border border-border flex items-center justify-center overflow-hidden max-w-md">
              <div className="text-center text-text-secondary/30">
                <div className="text-9xl mb-4">👤</div>
                <p className="font-sans text-sm">Dennis Reichenberg</p>
                <p className="font-sans text-xs mt-1">Head of AI @ VU SOLUTIONS</p>
              </div>
            </div>
          </motion.div>

          {/* Story */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="space-y-6"
          >
            <div>
              <p className="font-sans text-xs font-semibold uppercase tracking-widest text-gold mb-3">
                Meine Geschichte
              </p>
              <h2 className="font-serif text-h2-mobile lg:text-h2-desktop font-bold text-navy leading-tight">
                Technik trifft Strategie
              </h2>
            </div>

            <p className="font-sans text-body-lg text-text-secondary leading-relaxed">
              Seit 2023 arbeite ich als Softwareentwickler bei VU SOLUTIONS und
              wurde kürzlich zum <strong className="text-navy">Head of AI</strong>{" "}
              ernannt. In dieser Rolle berichte ich direkt an die
              Geschäftsführung und verantworte die Integration von KI in unsere
              Softwareprodukte sowie die Optimierung von Arbeitsprozessen.
            </p>

            <p className="font-sans text-body-md text-text-secondary leading-relaxed">
              Mein Weg hat mir gezeigt, wie wichtig es ist, die eigenen Stärken
              klar zu kommunizieren und strategisch zu verhandeln. Die
              Ernennung zum Head of AI war kein Zufall – sie war das Ergebnis
              gezielter Positionierung, kontinuierlicher Weiterentwicklung und
              der Fähigkeit, den eigenen Wert klar zu artikulieren.
            </p>

            <p className="font-sans text-body-md text-text-secondary leading-relaxed">
              Genau diese Erfahrungen bringe ich in meine Beratungstätigkeit
              ein. Ich kenne die Herausforderungen von Tech-Professionals aus
              erster Hand und verstehe, wie Unternehmen denken und entscheiden.
              Diese Perspektive macht meine Beratung besonders wertvoll.
            </p>

            <div className="grid grid-cols-2 gap-4 pt-2">
              {[
                { label: "Standort", value: "Ruhrgebiet" },
                { label: "Spezialisierung", value: "Tech & IT" },
                { label: "Sprachen", value: "Deutsch, Englisch" },
                { label: "Verfügbarkeit", value: "Online & vor Ort" },
              ].map((item) => (
                <div key={item.label} className="p-4 rounded-card bg-background">
                  <p className="font-sans text-xs text-text-secondary mb-1">
                    {item.label}
                  </p>
                  <p className="font-sans font-semibold text-navy text-sm">
                    {item.value}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
