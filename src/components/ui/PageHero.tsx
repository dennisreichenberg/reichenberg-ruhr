import { cn } from "@/lib/utils";
import { type ReactNode } from "react";

interface PageHeroProps {
  title: string;
  subtitle?: string;
  children?: ReactNode;
  className?: string;
}

export function PageHero({ title, subtitle, children, className }: PageHeroProps) {
  return (
    <section
      className={cn(
        "bg-navy pt-32 pb-20 lg:pt-40 lg:pb-28",
        className
      )}
    >
      <div className="container-site">
        <div className="max-w-3xl">
          <h1 className="font-serif text-h1-mobile lg:text-h1-desktop font-bold text-white mb-6 leading-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="font-sans text-body-lg text-white/75 leading-relaxed">
              {subtitle}
            </p>
          )}
          {children}
        </div>
      </div>
    </section>
  );
}
