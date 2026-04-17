"use client";

import { motion } from "framer-motion";
import { LinkButton } from "@/components/ui/Button";

export function AboutTeaser() {
  return (
    <section className="py-20 lg:py-28 bg-surface">
      <div className="container-site">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Image placeholder */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="relative"
          >
            <div className="aspect-square max-w-md mx-auto lg:mx-0 rounded-card bg-background border border-border flex items-center justify-center overflow-hidden">
              <div className="text-center text-text-secondary/30">
                <div className="text-9xl mb-4">👤</div>
                <p className="font-sans text-sm">Dennis Reichenberg</p>
              </div>
            </div>
            {/* Accent border */}
            <div className="absolute -bottom-4 -right-4 w-24 h-24 border-4 border-gold rounded-card hidden lg:block" />
          </motion.div>

          {/* Content */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <p className="font-sans text-xs font-semibold uppercase tracking-widest text-gold mb-4">
              Über mich
            </p>
            <h2 className="section-heading mb-6">
              Erfahrung trifft{" "}
              <span className="text-gold">Leidenschaft</span>
            </h2>
            <p className="font-sans text-body-lg text-text-secondary leading-relaxed mb-6">
              Als Head of AI bei VU SOLUTIONS und langjähriger Softwareentwickler
              kenne ich die Herausforderungen moderner Karrierewege aus eigener
              Erfahrung. Ich berate Sie mit fundiertem Wissen und ehrlicher
              Direktheit – stets auf Augenhöhe.
            </p>
            <p className="font-sans text-body-md text-text-secondary leading-relaxed mb-8">
              Mein Ziel: Ihr berufliches Potenzial vollständig entfalten – mit
              klaren Strategien, messbaren Ergebnissen und langfristiger
              Begleitung.
            </p>
            <LinkButton href="/ueber-mich" variant="secondary">
              Mehr über mich erfahren
            </LinkButton>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
