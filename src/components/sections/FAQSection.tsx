"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SectionHeader } from "@/components/ui/SectionHeader";

const faqs = [
  {
    question: "Wie läuft das kostenlose Erstgespräch ab?",
    answer:
      "Das Erstgespräch dauert ca. 30 Minuten und findet per Video-Call statt. Wir sprechen über Ihre aktuelle Situation, Ihre Ziele und klären, ob und wie ich Ihnen helfen kann. Es gibt keinerlei Verpflichtung.",
  },
  {
    question: "Wie lange dauert eine typische Beratung?",
    answer:
      "Das hängt von Ihren Zielen ab. Eine Gehaltsverhandlungsvorbereitung kann 2–3 Sessions umfassen, während eine umfassende Karriereplanung über mehrere Monate begleitet wird. Wir definieren gemeinsam, was sinnvoll ist.",
  },
  {
    question: "Arbeiten Sie nur mit IT-Fachleuten?",
    answer:
      "Nein. Mein Spezialgebiet ist zwar der IT- und Tech-Bereich, aber ich berate Fach- und Führungskräfte aus allen Branchen. Die Kernprinzipien von Karriereberatung und Gehaltsverhandlung sind universell.",
  },
  {
    question: "Was kostet die Beratung?",
    answer:
      "Die Preise variieren je nach Leistung und Umfang. Das Erstgespräch ist immer kostenlos. Danach erhalten Sie ein transparentes Angebot, das zu Ihrer Situation passt. Kontaktieren Sie mich für ein individuelles Angebot.",
  },
  {
    question: "Wie diskret ist die Beratung?",
    answer:
      "Absolute Diskretion ist selbstverständlich. Alles, was wir besprechen, bleibt streng vertraulich. Ich unterliege einer professionellen Schweigepflicht.",
  },
  {
    question: "Kann ich die Beratungskosten von der Steuer absetzen?",
    answer:
      "In vielen Fällen ja – Berufs- und Karriereberatung kann als Werbungskosten abgesetzt werden. Bitte sprechen Sie mit Ihrem Steuerberater für Ihre individuelle Situation.",
  },
];

function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border-b border-border">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between py-5 text-left gap-4 focus:outline-none group"
      >
        <span className="font-sans font-semibold text-navy group-hover:text-gold transition-colors">
          {question}
        </span>
        <span
          className={`text-gold text-xl shrink-0 transition-transform duration-300 ${
            isOpen ? "rotate-45" : ""
          }`}
        >
          +
        </span>
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <p className="font-sans text-sm text-text-secondary leading-relaxed pb-5">
              {answer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function FAQSection() {
  return (
    <section className="py-20 lg:py-28 bg-background">
      <div className="container-site">
        <SectionHeader
          eyebrow="FAQ"
          title="Häufige Fragen"
          subtitle="Antworten auf die wichtigsten Fragen zur Zusammenarbeit."
        />

        <div className="max-w-3xl">
          {faqs.map((faq) => (
            <FAQItem key={faq.question} {...faq} />
          ))}
        </div>
      </div>
    </section>
  );
}
