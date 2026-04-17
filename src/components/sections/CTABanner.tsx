"use client";

import { motion } from "framer-motion";
import { LinkButton } from "@/components/ui/Button";

export function CTABanner() {
  return (
    <section className="bg-gold py-16 lg:py-20">
      <div className="container-site">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          <h2 className="font-serif text-h2-mobile lg:text-h2-desktop font-bold text-white mb-4">
            Bereit für den nächsten Schritt?
          </h2>
          <p className="font-sans text-body-lg text-white/85 max-w-xl mx-auto mb-8">
            Vereinbaren Sie jetzt Ihr kostenloses Erstgespräch und erfahren Sie,
            wie ich Ihre Karriere nachhaltig voranbringen kann.
          </p>
          <LinkButton href="/kontakt" variant="ghost" size="lg">
            Kostenloses Erstgespräch buchen
          </LinkButton>
        </motion.div>
      </div>
    </section>
  );
}
