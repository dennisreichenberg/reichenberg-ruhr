import { cn } from "@/lib/utils";
import { type ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div className={cn("card p-6 lg:p-8", className)}>
      {children}
    </div>
  );
}

interface ServiceCardProps {
  icon: ReactNode;
  title: string;
  description: string;
  bullets?: string[];
}

export function ServiceCard({ icon, title, description, bullets }: ServiceCardProps) {
  return (
    <div className="card p-6 lg:p-8 flex flex-col gap-4">
      <div className="w-12 h-12 rounded-lg bg-navy/10 flex items-center justify-center text-navy text-2xl">
        {icon}
      </div>
      <h3 className="font-serif text-xl font-bold text-navy">{title}</h3>
      <p className="font-sans text-body-md text-text-secondary leading-relaxed">{description}</p>
      {bullets && bullets.length > 0 && (
        <ul className="space-y-1.5 mt-1">
          {bullets.map((b, i) => (
            <li key={i} className="flex items-start gap-2 font-sans text-sm text-text-secondary">
              <span className="text-gold mt-0.5">✓</span>
              {b}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
