// RTL helper. The assistant *replies* in the user's language (backend); this
// flips message direction for Arabic/Darija replies in the agent card.
export const RTL_LANGS: ReadonlySet<string> = new Set(["ar", "ary"]);

export function isRtl(language?: string): boolean {
  return language ? RTL_LANGS.has(language) : false;
}

// Agent-facing UI strings localized to the selected language (en/fr/darija), so
// switching the language select changes the greeting + input placeholder live.
const GREETING: Record<string, string> = {
  en: 'Ask me: "How much is left to my gate?"',
  fr: "Demandez-moi : « Combien reste-t-il jusqu'à ma porte ? »",
  darija: "سولني: \"شحال باقي للباب ديالي؟\"",
};

const PLACEHOLDER: Record<string, string> = {
  en: "Ask: how much is left to the gate?",
  fr: "Demandez : combien reste-t-il jusqu'à la porte ?",
  darija: "سول: شحال باقي للباب؟",
};

export const agentGreeting = (ui: string): string => GREETING[ui] ?? GREETING.en;
export const agentPlaceholder = (ui: string): string => PLACEHOLDER[ui] ?? PLACEHOLDER.en;
