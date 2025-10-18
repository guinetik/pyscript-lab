/**
 * Dynamically load example-specific translations
 * This allows us to keep individual example content in separate files
 * instead of bloating the main translation files
 */
import { writable } from 'svelte/store';
import { locale } from 'svelte-i18n';

/**
 * Load translations for a specific example (internal async function)
 * @param {string} exampleName - The example identifier (e.g., 'hello', 'digit-recognition')
 * @param {string} localeCode - The locale code (e.g., 'en', 'pt')
 * @returns {Promise<Object>} The example translations
 */
async function loadExampleTranslationsInternal(exampleName, localeCode) {
  try {
    const module = await import(
      `./locales/examples/${localeCode}/${exampleName}.json`
    );
    return module.default || module;
  } catch (error) {
    console.warn(
      `Failed to load example translations for ${exampleName} (${localeCode}):`,
      error
    );
    // Fallback to English if translation file doesn't exist
    if (localeCode !== 'en') {
      return loadExampleTranslationsInternal(exampleName, 'en');
    }
    return {};
  }
}

/**
 * Create a reactive store for example translations
 * Usage in a component:
 * const exampleTranslations = exampleTranslationStore('hello');
 *
 * Then use: {$exampleTranslations.title}
 *
 * @param {string} exampleName - The example identifier
 * @returns {import('svelte/store').Writable<Object>} Reactive store with translations
 */
export function exampleTranslationStore(exampleName) {
  const store = writable({});

  // Subscribe to locale changes and update store
  const unsubscribe = locale.subscribe(async ($locale) => {
    if ($locale) {
      const translations = await loadExampleTranslationsInternal(exampleName, $locale);
      store.set(translations);
    }
  });

  // Cleanup on unsubscribe
  return {
    subscribe: store.subscribe,
    unsubscribe
  };
}
