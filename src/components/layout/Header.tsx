"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/", label: "Start" },
  { href: "/leistungen", label: "Leistungen" },
  { href: "/ueber-mich", label: "Über mich" },
  { href: "/kontakt", label: "Kontakt" },
];

export function Header() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    setIsMobileOpen(false);
  }, [pathname]);

  return (
    <>
      <header
        className={cn(
          "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
          isScrolled
            ? "bg-surface shadow-md py-3"
            : "bg-surface/95 backdrop-blur-sm py-4"
        )}
      >
        <div className="container-site flex items-center justify-between">
          <Link
            href="/"
            className="font-serif text-xl font-bold text-navy hover:text-gold transition-colors"
          >
            Dennis Reichenberg
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "font-sans text-sm font-medium transition-colors hover:text-gold",
                  pathname === link.href
                    ? "text-gold"
                    : "text-text-primary"
                )}
              >
                {link.label}
              </Link>
            ))}
            <Link href="/kontakt" className="btn-primary text-sm px-5 py-2.5">
              Termin buchen
            </Link>
          </nav>

          {/* Mobile hamburger */}
          <button
            onClick={() => setIsMobileOpen(!isMobileOpen)}
            aria-label="Menü öffnen"
            className="lg:hidden flex flex-col gap-1.5 p-2 rounded"
          >
            <span
              className={cn(
                "block w-6 h-0.5 bg-navy transition-all duration-300",
                isMobileOpen && "rotate-45 translate-y-2"
              )}
            />
            <span
              className={cn(
                "block w-6 h-0.5 bg-navy transition-all duration-300",
                isMobileOpen && "opacity-0"
              )}
            />
            <span
              className={cn(
                "block w-6 h-0.5 bg-navy transition-all duration-300",
                isMobileOpen && "-rotate-45 -translate-y-2"
              )}
            />
          </button>
        </div>
      </header>

      {/* Mobile drawer */}
      <AnimatePresence>
        {isMobileOpen && (
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "tween", duration: 0.25 }}
            className="fixed inset-0 z-40 bg-surface pt-20 px-6 lg:hidden"
          >
            <nav className="flex flex-col gap-6 py-8">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "font-sans text-lg font-medium transition-colors hover:text-gold",
                    pathname === link.href ? "text-gold" : "text-text-primary"
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
            <div className="fixed bottom-8 left-6 right-6">
              <Link href="/kontakt" className="btn-primary w-full text-center">
                Termin buchen
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
