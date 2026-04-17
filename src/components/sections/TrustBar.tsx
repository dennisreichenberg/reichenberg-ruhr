"use client";

import { motion } from "framer-motion";

const stats = [
  { value: "3+", label: "Jahre Erfahrung" },
  { value: "50+", label: "Zufriedene Klienten" },
  { value: "95%", label: "Erfolgsquote" },
  { value: "100%", label: "Vertrauen & Diskretion" },
];

export function TrustBar() {
  return (
    <section className="bg-surface border-b border-border py-10">
      <div className="container-site">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="text-center"
            >
              <p className="font-serif text-4xl font-bold text-gold mb-1">
                {stat.value}
              </p>
              <p className="font-sans text-sm text-text-secondary">{stat.label}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
