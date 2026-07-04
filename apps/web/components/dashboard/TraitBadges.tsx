import { Badge } from "@/components/ui/badge";

const TRAITS = [
  "Analytical",
  "Goal-Driven",
  "Tech-First",
  "Founder Mindset",
  "Fast Learner",
  "Problem Solver",
] as const;

export function TraitBadges() {
  return (
    <div className="flex flex-wrap justify-center gap-2">
      {TRAITS.map((trait) => (
        <Badge
          key={trait}
          variant="default"
          className="bg-primary/20 text-primary hover:bg-primary/30"
        >
          {trait}
        </Badge>
      ))}
    </div>
  );
}
