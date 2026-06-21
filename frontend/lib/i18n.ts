// Minimal UI-label localization + RTL helper. The assistant *replies* in the
// user's language (backend); these labels are for the surrounding chrome.
import type { Language } from "./types";

export type UiLang = "en" | "fr" | "ar";

export const RTL_LANGS: ReadonlySet<string> = new Set(["ar", "ary"]);

export function isRtl(language?: string): boolean {
  return language ? RTL_LANGS.has(language) : false;
}

type LabelKey =
  | "title"
  | "subtitle"
  | "placeholder"
  | "send"
  | "listening"
  | "tapToSpeak"
  | "stop"
  | "thinking"
  | "airport"
  | "toolTrace"
  | "you"
  | "assistant"
  | "emptyHint"
  | "error";

export const LABELS: Record<UiLang, Record<LabelKey, string>> = {
  en: {
    title: "Airport Wayfinding Assistant",
    subtitle: "Ask about gates, flights, and services — by voice or text.",
    placeholder: "Type your question…",
    send: "Send",
    listening: "Listening…",
    tapToSpeak: "Tap to speak",
    stop: "Stop",
    thinking: "Thinking…",
    airport: "Airport",
    toolTrace: "Tool trace",
    you: "You",
    assistant: "Assistant",
    emptyHint: "Try: \"Where is my gate for flight SV-624?\"",
    error: "Something went wrong. Is the backend running?",
  },
  fr: {
    title: "Assistant d'orientation aéroport",
    subtitle: "Portes, vols et services — par voix ou texte.",
    placeholder: "Saisissez votre question…",
    send: "Envoyer",
    listening: "Écoute…",
    tapToSpeak: "Appuyez pour parler",
    stop: "Arrêter",
    thinking: "Réflexion…",
    airport: "Aéroport",
    toolTrace: "Trace des outils",
    you: "Vous",
    assistant: "Assistant",
    emptyHint: "Essayez : « Où est ma porte pour le vol SV-624 ? »",
    error: "Une erreur s'est produite. Le backend est-il lancé ?",
  },
  ar: {
    title: "مساعد التنقل في المطار",
    subtitle: "اسأل عن البوابات والرحلات والخدمات — صوتاً أو نصاً.",
    placeholder: "اكتب سؤالك…",
    send: "إرسال",
    listening: "يستمع…",
    tapToSpeak: "اضغط للتحدث",
    stop: "إيقاف",
    thinking: "يفكر…",
    airport: "المطار",
    toolTrace: "أثر الأدوات",
    you: "أنت",
    assistant: "المساعد",
    emptyHint: "جرّب: «أين بوابتي للرحلة SV-624؟»",
    error: "حدث خطأ ما. هل الخادم يعمل؟",
  },
};

export function labels(ui: UiLang) {
  return LABELS[ui];
}

export function uiDir(ui: UiLang): "rtl" | "ltr" {
  return ui === "ar" ? "rtl" : "ltr";
}
