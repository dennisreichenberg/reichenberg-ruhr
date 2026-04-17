"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

const schema = z.object({
  name: z.string().min(2, "Bitte geben Sie Ihren Namen ein."),
  email: z.string().email("Bitte geben Sie eine gültige E-Mail-Adresse ein."),
  subject: z.string().min(3, "Bitte wählen Sie ein Thema."),
  message: z.string().min(20, "Bitte schreiben Sie mindestens 20 Zeichen."),
  privacy: z.literal(true, {
    errorMap: () => ({ message: "Bitte stimmen Sie der Datenschutzerklärung zu." }),
  }),
});

type FormData = z.infer<typeof schema>;

const subjects = [
  "Gehaltsverhandlung",
  "Karriereplanung",
  "Bewerbungscoaching",
  "Berufliche Neuorientierung",
  "KI & Tech-Karriere",
  "Führungskräfte-Entwicklung",
  "Sonstiges",
];

const contactInfo = [
  {
    icon: "✉️",
    label: "E-Mail",
    value: "info@reichenberg.ruhr",
    href: "mailto:info@reichenberg.ruhr",
  },
  {
    icon: "🔗",
    label: "LinkedIn",
    value: "linkedin.com/in/dennis-reichenberg",
    href: "https://www.linkedin.com/in/dennis-reichenberg",
  },
  {
    icon: "📍",
    label: "Standort",
    value: "Ruhrgebiet, Deutschland",
    href: null,
  },
  {
    icon: "⏰",
    label: "Erreichbarkeit",
    value: "Mo–Fr, 9–18 Uhr",
    href: null,
  },
];

export function ContactSection() {
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setSubmitting(true);
    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (res.ok) {
        setSubmitted(true);
      }
    } catch {
      // silently handle
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="py-20 lg:py-28 bg-background">
      <div className="container-site">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20">
          {/* Contact info */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="section-heading mb-6">Direkt in Kontakt treten</h2>
            <p className="font-sans text-body-md text-text-secondary leading-relaxed mb-8">
              Schreiben Sie mir eine Nachricht oder buchen Sie direkt einen
              Termin über den Kalender. Das Erstgespräch ist immer kostenlos.
            </p>

            <ul className="space-y-5 mb-10">
              {contactInfo.map((item) => (
                <li key={item.label} className="flex items-start gap-4">
                  <span className="text-2xl shrink-0 mt-0.5">{item.icon}</span>
                  <div>
                    <p className="font-sans text-xs text-text-secondary mb-0.5">
                      {item.label}
                    </p>
                    {item.href ? (
                      <a
                        href={item.href}
                        target={item.href.startsWith("http") ? "_blank" : undefined}
                        rel={
                          item.href.startsWith("http")
                            ? "noopener noreferrer"
                            : undefined
                        }
                        className="font-sans font-medium text-navy hover:text-gold transition-colors"
                      >
                        {item.value}
                      </a>
                    ) : (
                      <p className="font-sans font-medium text-navy">
                        {item.value}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ul>

            {/* Cal.com embed placeholder */}
            <div className="rounded-card border border-border bg-surface p-6">
              <h3 className="font-serif text-lg font-bold text-navy mb-3">
                Direktbuchung
              </h3>
              <p className="font-sans text-sm text-text-secondary mb-4">
                Buchen Sie direkt einen Termin für Ihr kostenloses Erstgespräch:
              </p>
              <div
                className="bg-background rounded-field p-4 text-center text-text-secondary/50 text-sm border border-border"
                style={{ minHeight: 200 }}
              >
                {/* Cal.com integration via script embed */}
                <p className="mt-16 font-sans">
                  📅 Kalender-Integration (Cal.com)
                </p>
                <p className="text-xs mt-2">
                  Wird nach Konfiguration aktiviert
                </p>
              </div>
            </div>
          </motion.div>

          {/* Contact form */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            {submitted ? (
              <div className="card p-8 text-center">
                <div className="text-5xl mb-4">✅</div>
                <h3 className="font-serif text-2xl font-bold text-navy mb-3">
                  Nachricht gesendet!
                </h3>
                <p className="font-sans text-body-md text-text-secondary">
                  Vielen Dank für Ihre Nachricht. Ich melde mich in der Regel
                  innerhalb von 24 Stunden bei Ihnen.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="card p-6 lg:p-8 space-y-5">
                <h3 className="font-serif text-xl font-bold text-navy mb-1">
                  Nachricht senden
                </h3>

                {/* Name */}
                <div>
                  <label className="font-sans text-sm font-medium text-text-primary block mb-1.5">
                    Name *
                  </label>
                  <input
                    {...register("name")}
                    type="text"
                    placeholder="Ihr vollständiger Name"
                    className={cn(
                      "form-field",
                      errors.name && "border-red-400 focus:ring-red-400 focus:border-red-400"
                    )}
                  />
                  {errors.name && (
                    <p className="font-sans text-xs text-red-500 mt-1">
                      {errors.name.message}
                    </p>
                  )}
                </div>

                {/* Email */}
                <div>
                  <label className="font-sans text-sm font-medium text-text-primary block mb-1.5">
                    E-Mail *
                  </label>
                  <input
                    {...register("email")}
                    type="email"
                    placeholder="ihre@email.de"
                    className={cn(
                      "form-field",
                      errors.email && "border-red-400 focus:ring-red-400 focus:border-red-400"
                    )}
                  />
                  {errors.email && (
                    <p className="font-sans text-xs text-red-500 mt-1">
                      {errors.email.message}
                    </p>
                  )}
                </div>

                {/* Subject */}
                <div>
                  <label className="font-sans text-sm font-medium text-text-primary block mb-1.5">
                    Thema *
                  </label>
                  <select
                    {...register("subject")}
                    className={cn(
                      "form-field",
                      errors.subject && "border-red-400 focus:ring-red-400 focus:border-red-400"
                    )}
                  >
                    <option value="">Bitte wählen…</option>
                    {subjects.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                  {errors.subject && (
                    <p className="font-sans text-xs text-red-500 mt-1">
                      {errors.subject.message}
                    </p>
                  )}
                </div>

                {/* Message */}
                <div>
                  <label className="font-sans text-sm font-medium text-text-primary block mb-1.5">
                    Nachricht *
                  </label>
                  <textarea
                    {...register("message")}
                    rows={5}
                    placeholder="Beschreiben Sie kurz Ihre Situation und was Sie sich von der Beratung wünschen…"
                    className={cn(
                      "form-field resize-none",
                      errors.message && "border-red-400 focus:ring-red-400 focus:border-red-400"
                    )}
                  />
                  {errors.message && (
                    <p className="font-sans text-xs text-red-500 mt-1">
                      {errors.message.message}
                    </p>
                  )}
                </div>

                {/* Privacy */}
                <div>
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      {...register("privacy")}
                      type="checkbox"
                      className="mt-1 w-4 h-4 rounded border-border accent-gold cursor-pointer"
                    />
                    <span className="font-sans text-xs text-text-secondary leading-relaxed">
                      Ich stimme der Verarbeitung meiner Daten gemäß der{" "}
                      <a href="/datenschutz" className="text-gold hover:underline">
                        Datenschutzerklärung
                      </a>{" "}
                      zu. *
                    </span>
                  </label>
                  {errors.privacy && (
                    <p className="font-sans text-xs text-red-500 mt-1">
                      {errors.privacy.message}
                    </p>
                  )}
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  disabled={submitting}
                  className="w-full"
                >
                  {submitting ? "Wird gesendet…" : "Nachricht senden"}
                </Button>
              </form>
            )}
          </motion.div>
        </div>
      </div>
    </section>
  );
}
