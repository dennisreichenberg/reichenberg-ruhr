"use client";

import { motion } from "framer-motion";
import { SectionHeader } from "@/components/ui/SectionHeader";

const services = [
  {
    icon: "💼",
    title: "Gehaltsverhandlung",
    description:
      "Ich helfe Ihnen, das Gehalt zu bekommen, das Sie verdienen. Mit konkreten Strategien, marktgerechten Argumenten und gezieltem Verhandlungstraining.",
    bullets: [
      "Marktgerechte Gehaltsanalyse",
      "Individuelle Verhandlungsstrategie",
      "Formulierungshilfen & Rollenspiele",
      "Nachverhandlung & Follow-up",
    ],
  },
  {
    icon: "🎯",
    title: "Karriereplanung",
    description:
      "Gemeinsam analysieren wir Ihren aktuellen Stand, definieren realistische Ziele und entwickeln einen klaren Fahrplan für Ihre berufliche Zukunft.",
    bullets: [
      "Stärken- & Potenzialanalyse",
      "Karriereziel-Entwicklung",
      "Persönliche Roadmap",
      "Quartalsweise Fortschrittsgespräche",
    ],
  },
  {
    icon: "📋",
    title: "Bewerbungscoaching",
    description:
      "Professionelle Unterstützung vom Lebenslauf bis zum Jobangebot. Ich optimiere Ihre Unterlagen und bereite Sie gezielt auf Interviews vor.",
    bullets: [
      "CV-Analyse & Optimierung",
      "Anschreiben-Feedback",
      "LinkedIn-Profil-Optimierung",
      "Interview-Simulation & Feedback",
    ],
  },
  {
    icon: "🔄",
    title: "Berufliche Neuorientierung",
    description:
      "Sie möchten sich beruflich neu ausrichten? Ich begleite Sie durch diesen Prozess – von der Entscheidungsfindung bis zum erfolgreichen Wechsel.",
    bullets: [
      "Branchenanalyse & Transferpotenzial",
      "Qualifikationslücken-Analyse",
      "Umschulungs- & Weiterbildungsberatung",
      "Netzwerkaufbau-Strategie",
    ],
  },
  {
    icon: "🤖",
    title: "KI & Tech-Karriere-Coaching",
    description:
      "Als Head of AI kenne ich den Tech-Markt aus dem Inneren. Ich berate Tech-Professionals bei Karriereschritten im KI- und IT-Bereich.",
    bullets: [
      "Tech-Gehaltsverhandlung",
      "Karrierepfade in der KI-Branche",
      "Positionierung als Tech-Leader",
      "Portfolio & GitHub-Optimierung",
    ],
  },
  {
    icon: "📈",
    title: "Führungskräfte-Entwicklung",
    description:
      "Der Schritt zur Führungskraft erfordert neue Kompetenzen. Ich unterstütze Sie beim Aufbau Ihrer Führungsidentität und beim erfolgreichen Einstieg.",
    bullets: [
      "Leadership-Positionierung",
      "Gehaltsverhandlung auf C-Level",
      "Stakeholder-Management",
      "Persönliche Markenbildung",
    ],
  },
];

export function ServicesGrid() {
  return (
    <section className="py-20 lg:py-28 bg-background">
      <div className="container-site">
        <SectionHeader
          eyebrow="Was ich anbiete"
          title="Alle Leistungen im Überblick"
          subtitle="Jede Beratung ist individuell auf Ihre Situation und Ziele zugeschnitten."
        />

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {services.map((service, i) => (
            <motion.div
              key={service.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: (i % 3) * 0.1, duration: 0.5 }}
              className="card p-6 lg:p-8 flex flex-col gap-4"
            >
              <div className="w-12 h-12 rounded-lg bg-navy/10 flex items-center justify-center text-2xl">
                {service.icon}
              </div>
              <h3 className="font-serif text-xl font-bold text-navy">
                {service.title}
              </h3>
              <p className="font-sans text-sm text-text-secondary leading-relaxed">
                {service.description}
              </p>
              <ul className="space-y-1.5 mt-1">
                {service.bullets.map((b) => (
                  <li
                    key={b}
                    className="flex items-start gap-2 font-sans text-sm text-text-secondary"
                  >
                    <span className="text-gold mt-0.5 shrink-0">✓</span>
                    {b}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
