// RTL helper. The assistant *replies* in the user's language (backend); this
// flips message direction for Arabic/Darija replies in the agent card.
export const RTL_LANGS: ReadonlySet<string> = new Set(["ar", "ary"]);

export function isRtl(language?: string): boolean {
  return language ? RTL_LANGS.has(language) : false;
}
