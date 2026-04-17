import Link from "next/link";

const footerLinks = {
  navigation: [
    { href: "/", label: "Start" },
    { href: "/leistungen", label: "Leistungen" },
    { href: "/ueber-mich", label: "Über mich" },
    { href: "/kontakt", label: "Kontakt" },
  ],
  legal: [
    { href: "/impressum", label: "Impressum" },
    { href: "/datenschutz", label: "Datenschutz" },
  ],
};

export function Footer() {
  return (
    <footer className="bg-navy text-white">
      <div className="container-site py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          {/* Brand */}
          <div>
            <p className="font-serif text-xl font-bold text-white mb-3">
              Dennis Reichenberg
            </p>
            <p className="font-sans text-sm text-white/70 leading-relaxed">
              Berufliche Beratung & Karriere-Coaching für Fach- und Führungskräfte.
            </p>
          </div>

          {/* Navigation */}
          <div>
            <p className="font-sans text-xs font-semibold uppercase tracking-widest text-white/50 mb-4">
              Navigation
            </p>
            <ul className="space-y-2">
              {footerLinks.navigation.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="font-sans text-sm text-white/70 hover:text-gold transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <p className="font-sans text-xs font-semibold uppercase tracking-widest text-white/50 mb-4">
              Kontakt
            </p>
            <ul className="space-y-2">
              <li>
                <a
                  href="mailto:info@reichenberg.ruhr"
                  className="font-sans text-sm text-white/70 hover:text-gold transition-colors"
                >
                  info@reichenberg.ruhr
                </a>
              </li>
              <li>
                <a
                  href="https://www.linkedin.com/in/dennis-reichenberg"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-sans text-sm text-white/70 hover:text-gold transition-colors"
                >
                  LinkedIn
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="font-sans text-xs text-white/40">
            © {new Date().getFullYear()} Dennis Reichenberg. Alle Rechte vorbehalten.
          </p>
          <ul className="flex gap-6">
            {footerLinks.legal.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="font-sans text-xs text-white/40 hover:text-white/70 transition-colors"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </footer>
  );
}
