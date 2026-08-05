import { Badge } from "@/components/ui/badge";

const DEFAULT_TRAITS: string[] = [
  "Analytical",
  "Goal-Driven",
  "Tech-First",
  "Problem Solver",
];

interface TraitBadgesProps {
  traits?: string[];
}

export function TraitBadges({ traits = DEFAULT_TRAITS }: TraitBadgesProps) {
  const displayTraits = traits.length > 0 ? traits : DEFAULT_TRAITS;

  return (
    <div className="flex flex-wrap justify-center gap-2">
      {displayTraits.map((trait) => (
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
