import type { Metadata } from "next";
import { PageHero } from "@/components/ui/PageHero";

export const metadata: Metadata = {
  title: "Datenschutz",
  description: "Datenschutzerklärung – Dennis Reichenberg Berufliche Beratung",
};

export default function DatenschutzPage() {
  return (
    <>
      <PageHero title="Datenschutzerklärung" />
      <section className="py-16 bg-background">
        <div className="container-site max-w-3xl">
          <div className="card p-8 space-y-6">
            <div>
              <h2 className="font-serif text-xl font-bold text-navy mb-3">1. Datenschutz auf einen Blick</h2>
              <p className="font-sans text-sm text-text-secondary leading-relaxed">
                Diese Datenschutzerklärung klärt Sie über die Art, den Umfang und Zweck der Verarbeitung von
                personenbezogenen Daten auf dieser Website auf. Personenbezogene Daten sind alle Daten, mit denen Sie
                persönlich identifiziert werden können.
              </p>
            </div>

            <div>
              <h2 className="font-serif text-xl font-bold text-navy mb-3">2. Kontaktformular</h2>
              <p className="font-sans text-sm text-text-secondary leading-relaxed">
                Wenn Sie das Kontaktformular nutzen, werden die eingegebenen Daten (Name, E-Mail, Nachricht)
                zur Bearbeitung Ihrer Anfrage verarbeitet. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO.
                Die Daten werden nicht an Dritte weitergegeben und nach Abschluss der Bearbeitung gelöscht.
              </p>
            </div>

            <div>
              <h2 className="font-serif text-xl font-bold text-navy mb-3">3. Hosting</h2>
              <p className="font-sans text-sm text-text-secondary leading-relaxed">
                Diese Website wird bei Vercel, Inc. gehostet. Die Verarbeitung erfolgt auf Basis von Art. 6 Abs. 1
                lit. f DSGVO (berechtigtes Interesse an zuverlässiger Website-Auslieferung). Ein
                Auftragsverarbeitungsvertrag wurde geschlossen.
              </p>
            </div>

            <div>
              <h2 className="font-serif text-xl font-bold text-navy mb-3">4. Ihre Rechte</h2>
              <p className="font-sans text-sm text-text-secondary leading-relaxed">
                Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung,
                Datenübertragbarkeit und Widerspruch. Wenden Sie sich dazu an: info@reichenberg.ruhr
              </p>
            </div>

            <p className="font-sans text-xs text-text-secondary italic">
              Hinweis: Diese Datenschutzerklärung ist ein Platzhalter. Bitte lassen Sie sie von einem Rechtsanwalt
              prüfen und vervollständigen.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
