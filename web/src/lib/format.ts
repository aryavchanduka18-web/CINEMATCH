export const LANGUAGES: Record<string, string> = {
  en: "English", hi: "Hindi", ta: "Tamil", te: "Telugu", ml: "Malayalam", kn: "Kannada", bn: "Bengali",
  mr: "Marathi", ko: "Korean", ja: "Japanese", es: "Spanish", fr: "French", de: "German", it: "Italian",
  zh: "Mandarin", cn: "Cantonese", pt: "Portuguese", tr: "Turkish", fa: "Persian", ru: "Russian",
  sv: "Swedish", da: "Danish", no: "Norwegian", fi: "Finnish", pl: "Polish", nl: "Dutch",
};

export const languageName = (code?: string | null) => (code ? LANGUAGES[code] ?? code.toUpperCase() : "");

export function runtime(min?: number | null): string {
  if (!min) return "";
  const h = Math.floor(min / 60);
  const m = min % 60;
  return h ? `${h}h ${m}m` : `${m}m`;
}