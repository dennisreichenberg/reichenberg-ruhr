import type { Metadata } from "next";
import { PageHero } from "@/components/ui/PageHero";

export const metadata: Metadata = {
  title: "Impressum",
  description: "Impressum – Dennis Reichenberg Berufliche Beratung",
};

export default function ImpressumPage() {
  return (
    <>
      <PageHero title="Impressum" />
      <section className="py-16 bg-background">
        <div className="container-site max-w-3xl">
          <div className="card p-8 prose prose-slate max-w-none">
            <h2 className="font-serif text-xl font-bold text-navy">Angaben gemäß § 5 TMG</h2>
            <p className="font-sans text-text-secondary text-sm leading-relaxed">
              Dennis Reichenberg<br />
              [Straße und Hausnummer]<br />
              [PLZ] [Ort]<br />
              Deutschland
            </p>
            <h2 className="font-serif text-xl font-bold text-navy mt-6">Kontakt</h2>
            <p className="font-sans text-text-secondary text-sm leading-relaxed">
              E-Mail: info@reichenberg.ruhr
            </p>
            <p className="font-sans text-xs text-text-secondary mt-6 italic">
              Hinweis: Dieses Impressum ist ein Platzhalter und muss mit den vollständigen Angaben ausgefüllt werden.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
