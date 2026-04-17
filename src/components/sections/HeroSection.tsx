"use client";

import { motion } from "framer-motion";
import { LinkButton } from "@/components/ui/Button";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (delay: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: "easeOut", delay },
  }),
};

export function HeroSection() {
  return (
    <section className="relative bg-navy min-h-screen flex items-center pt-24 pb-20 overflow-hidden">
      {/* Subtle background pattern */}
      <div
        aria-hidden
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage:
            "radial-gradient(circle at 80% 20%, #C9922A 0%, transparent 50%)",
        }}
      />

      <div className="container-site relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Text */}
          <div>
            <motion.p
              custom={0}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              className="font-sans text-xs font-semibold uppercase tracking-widest text-gold mb-4"
            >
              Berufliche Beratung & Karriere-Coaching
            </motion.p>

            <motion.h1
              custom={0.1}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              className="font-serif text-h1-mobile lg:text-h1-desktop font-bold text-white leading-tight mb-6"
            >
              Ihre Karriere.{" "}
              <span className="text-gold">Strategisch geplant.</span>
            </motion.h1>

            <motion.p
              custom={0.2}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              className="font-sans text-body-lg text-white/75 leading-relaxed mb-8 max-w-lg"
            >
              Als erfahrener Karriereberater unterstütze ich Fach- und
              Führungskräfte bei Gehaltsverhandlungen, Karriereplanung und
              beruflicher Neuorientierung. Mit Strategie zum Erfolg.
            </motion.p>

            <motion.div
              custom={0.3}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              className="flex flex-col sm:flex-row gap-4"
            >
              <LinkButton href="/kontakt" variant="primary" size="lg">
                Kostenloses Erstgespräch
              </LinkButton>
              <LinkButton href="/leistungen" variant="ghost" size="lg">
                Leistungen entdecken
              </LinkButton>
            </motion.div>
          </div>

          {/* Avatar placeholder */}
          <motion.div
            custom={0.2}
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            className="hidden lg:flex justify-center"
          >
            <div className="relative">
              <div className="w-80 h-80 rounded-full bg-navy-light border-4 border-gold/30 flex items-center justify-center overflow-hidden shadow-2xl">
                <div className="text-center text-white/30">
                  <div className="text-8xl mb-2">👤</div>
                  <p className="text-sm font-sans">Dennis Reichenberg</p>
                </div>
              </div>
              {/* Decorative ring */}
              <div className="absolute -inset-4 rounded-full border border-gold/20 pointer-events-none" />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
