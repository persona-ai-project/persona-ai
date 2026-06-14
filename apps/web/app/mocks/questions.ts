export interface OnboardingQuestion {
  id: string;
  text: string;
}

export const onboardingQuestions: OnboardingQuestion[] = [
  {
    id: "1",
    text: "What is your name and what do you do professionally?",
  },
  {
    id: "2",
    text: "What are your biggest passions or interests outside of work?",
  },
  {
    id: "3",
    text: "How would your closest friends describe your personality?",
  },
  {
    id: "4",
    text: "What are your core values and beliefs that guide your decisions?",
  },
  {
    id: "5",
    text: "What is your biggest goal for the next 12 months?",
  },
];

export const personaTraits = [
  "Analytical Thinker",
  "Goal Oriented",
  "Tech Enthusiast",
] as const;
