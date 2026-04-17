import type { Metadata } from "next";
import { PageHero } from "@/components/ui/PageHero";
import { StorySection } from "@/components/sections/StorySection";
import { TimelineSection } from "@/components/sections/TimelineSection";
import { ValuesSection } from "@/components/sections/ValuesSection";
import { CTABanner } from "@/components/sections/CTABanner";

export const metadata: Metadata = {
  title: "Über mich",
  description:
    "Dennis Reichenberg – Head of AI, Softwareentwickler und Karriereberater aus dem Ruhrgebiet. Erfahren Sie mehr über meinen Werdegang und meine Werte.",
};

export default function UeberMichPage() {
  return (
    <>
      <PageHero
        title="Über mich"
        subtitle="Von der Softwareentwicklung zur Karriereberatung – mein Weg und meine Werte."
      />
      <StorySection />
      <TimelineSection />
      <ValuesSection />
      <CTABanner />
    </>
  );
}
