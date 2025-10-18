/**
 * Internationalization configuration for PyScript Lab.
 * Initializes svelte-i18n with locale detection and fallback handling.
 * @module i18n
 */
import { register, init, getLocaleFromNavigator, locale } from 'svelte-i18n';

// Register locale loaders
register('en', () => import('./locales/en.json'));
register('pt', () => import('./locales/pt.json'));

/**
 * Get stored locale from localStorage or browser preference
 * Supports: English (en), Portuguese (pt)
 * Falls back to English for unsupported languages
 * @returns {string} The locale code
 */
function getInitialLocale() {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('pyscript-lab-locale');
    if (stored) return stored;
  }

  // Detect browser language
  const browserLang = getLocaleFromNavigator();

  // Only support EN and PT; fallback to EN
  if (browserLang && browserLang.startsWith('pt')) {
    return 'pt';
  }

  return 'en';
}

/**
 * Initialize i18n with fallback and locale detection
 * @returns {void}
 */
export function initializeI18n() {
  init({
    fallbackLocale: 'en',
    initialLocale: getInitialLocale(),
  });
}

/**
 * Change the current locale and persist to localStorage
 * @param {string} newLocale - The locale code to switch to
 * @returns {void}
 */
export function changeLocale(newLocale) {
  locale.set(newLocale);
  if (typeof window !== 'undefined') {
    localStorage.setItem('pyscript-lab-locale', newLocale);
    // Update HTML lang attribute for accessibility
    document.documentElement.lang = newLocale;
  }
}

/**
 * Available locales configuration
 */
export const AVAILABLE_LOCALES = {
  en: { code: 'en', name: 'English', flag: '🇺🇸' },
  pt: { code: 'pt', name: 'Português', flag: '🇧🇷' },
};
