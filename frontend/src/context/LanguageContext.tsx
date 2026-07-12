import { createContext, useContext, useState, type ReactNode } from "react";
import { en, fr, type Language, type Translations } from "../lib/i18n";

const STORAGE_KEY = "presence.language";

interface LanguageContextValue {
  language: Language;
  toggleLanguage: () => void;
  t: Translations;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

function getInitialLanguage(): Language {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "en" || stored === "fr") return stored;
  return navigator.language.toLowerCase().startsWith("fr") ? "fr" : "en";
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(getInitialLanguage);

  function toggleLanguage() {
    setLanguage((current) => {
      const next = current === "en" ? "fr" : "en";
      localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  }

  return (
    <LanguageContext.Provider value={{ language, toggleLanguage, t: language === "fr" ? fr : en }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider");
  return ctx;
}
