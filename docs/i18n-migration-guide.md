# i18n Migration Guide

This guide provides step-by-step instructions for implementing i18n in the PyScript Lab application.

## Prerequisites

- Node.js 18+ installed
- Familiarity with Svelte and SvelteKit
- Understanding of the project structure

## Step-by-Step Implementation

### Step 1: Install Dependencies

```bash
npm install svelte-i18n
```

### Step 2: Create i18n Infrastructure

#### 2.1 Create Directory Structure

```bash
mkdir -p src/lib/i18n/locales
```

#### 2.2 Create i18n Configuration

Create `src/lib/i18n/index.js`:

```javascript
/**
 * Internationalization configuration for PyScript Lab.
 * @module i18n
 */
import { register, init, getLocaleFromNavigator, locale } from 'svelte-i18n';

// Register locale loaders
register('en', () => import('./locales/en.json'));
register('es', () => import('./locales/es.json'));
register('pt', () => import('./locales/pt.json'));

/**
 * Get stored locale from localStorage or browser preference
 * @returns {string} The locale code
 */
function getInitialLocale() {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('pyscript-lab-locale');
    if (stored) return stored;
  }
  return getLocaleFromNavigator();
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
    document.documentElement.lang = newLocale;
  }
}

/**
 * Available locales configuration
 */
export const AVAILABLE_LOCALES = {
  en: { code: 'en', name: 'English', flag: '🇺🇸' },
  es: { code: 'es', name: 'Español', flag: '🇪🇸' },
  pt: { code: 'pt', name: 'Português', flag: '🇧🇷' },
};
```

#### 2.3 Create Base Translation Files

Create `src/lib/i18n/locales/en.json` with all English strings (see i18n-code-examples.md for full content).

Create `src/lib/i18n/locales/es.json` and `src/lib/i18n/locales/pt.json` with initial translations.

### Step 3: Update Root Layout

**File**: `src/routes/+layout.svelte`

**Before**:
```svelte
<script>
  import '../app.css';
  import Nav from '../lib/components/Nav.svelte';

  let { children } = $props();
</script>

<Nav />

<main class="flex h-[calc(100%-120px)] w-full flex-col justify-center">
  {@render children()}
</main>
```

**After**:
```svelte
<script>
  import '../app.css';
  import Nav from '../lib/components/Nav.svelte';
  import { initializeI18n } from '$lib/i18n';
  import { isLoading } from 'svelte-i18n';

  let { children } = $props();

  // Initialize i18n
  initializeI18n();

  // Update HTML lang attribute when locale changes
  $effect(() => {
    if (!$isLoading && typeof document !== 'undefined') {
      import('svelte-i18n').then(({ locale }) => {
        locale.subscribe(value => {
          if (value) {
            document.documentElement.lang = value;
          }
        });
      });
    }
  });
</script>

{#if $isLoading}
  <div class="flex h-screen w-full items-center justify-center">
    <div class="text-center">
      <div class="mb-4 text-4xl">🐍</div>
      <div class="text-xl font-semibold text-gray-700">Loading...</div>
    </div>
  </div>
{:else}
  <Nav />
  <main class="flex h-[calc(100%-120px)] w-full flex-col justify-center">
    {@render children()}
  </main>
{/if}
```

### Step 4: Create Language Switcher Component

Create `src/lib/components/LanguageSwitcher.svelte`:

```svelte
<script>
  /**
   * Language switcher dropdown component.
   * Allows users to change the application locale and persists the selection.
   */
  import { locale } from 'svelte-i18n';
  import { AVAILABLE_LOCALES, changeLocale } from '$lib/i18n';

  let isOpen = $state(false);

  function toggleDropdown() {
    isOpen = !isOpen;
  }

  function closeDropdown() {
    isOpen = false;
  }

  function selectLocale(newLocale) {
    changeLocale(newLocale);
    closeDropdown();
  }

  $: currentLocale = $locale || 'en';
  $: currentLanguage = AVAILABLE_LOCALES[currentLocale];
</script>

<div class="relative">
  <button
    onclick={toggleDropdown}
    class="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-gray-100 transition-colors"
    aria-label="Select language"
    aria-expanded={isOpen}
    aria-haspopup="true"
  >
    <span class="text-xl">{currentLanguage?.flag}</span>
    <span class="font-medium text-gray-700">{currentLanguage?.name}</span>
    <svg
      class="h-4 w-4 transition-transform {isOpen ? 'rotate-180' : ''}"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
    </svg>
  </button>

  {#if isOpen}
    <div
      class="absolute right-0 mt-2 w-48 rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5 z-50"
      role="menu"
    >
      <div class="py-1">
        {#each Object.values(AVAILABLE_LOCALES) as language}
          <button
            onclick={() => selectLocale(language.code)}
            class="block w-full text-left px-4 py-2 text-sm hover:bg-gray-100 {currentLocale === language.code ? 'bg-yellow-50 text-yellow-600 font-bold' : 'text-gray-700'}"
            role="menuitem"
          >
            <span class="mr-2">{language.flag}</span>
            {language.name}
          </button>
        {/each}
      </div>
    </div>
  {/if}
</div>

{#if isOpen}
  <button
    class="fixed inset-0 z-40"
    onclick={closeDropdown}
    aria-label="Close dropdown"
    tabindex="-1"
  ></button>
{/if}
```

### Step 5: Update Navigation Component

**File**: `src/lib/components/Nav.svelte`

**Changes needed**:

1. Import the translation function:
```javascript
import { t } from 'svelte-i18n';
import LanguageSwitcher from './LanguageSwitcher.svelte';
```

2. Replace hardcoded strings with translation calls:

**Before**:
```svelte
<button
  class="h-6 w-6"
  on:click={toggleMenu}
  aria-label="Toggle menu"
>
```

**After**:
```svelte
<button
  class="h-6 w-6"
  on:click={toggleMenu}
  aria-label={$t('nav.toggleMenu')}
>
```

3. Add language switcher to desktop navigation (in the right section):
```svelte
<div class="hidden items-center space-x-3 md:flex">
  <!-- Language Switcher -->
  <LanguageSwitcher />
  
  <!-- existing badges and links -->
</div>
```

4. Add language switcher to mobile navigation (at the top of the mobile menu):
```svelte
<ul class="...">
  <div class="border-b border-inherit p-4">
    <LanguageSwitcher />
  </div>
  <!-- existing menu items -->
</ul>
```

5. Update visitor count badge:

**Before**:
```svelte
<img
  src={`https://img.shields.io/static/v1?label=&message=${visits} Visitors&color=blueviolet&style=flat-square`}
  alt="Visits"
/>
```

**After**:
```svelte
<img
  src={`https://img.shields.io/static/v1?label=&message=${$t('nav.visitors', { values: { count: visits } })}&color=blueviolet&style=flat-square`}
  alt={$t('nav.visitors', { values: { count: visits } })}
/>
```

### Step 6: Update ExperimentCard Component

**File**: `src/lib/components/ExperimentCard.svelte`

**Changes needed**:

1. Import translation function:
```javascript
import { t } from 'svelte-i18n';
```

2. Update button labels:

**Before**:
```svelte
<a
  href={getLink(props.previousPage)}
  class="..."
>
  <img class="inline h-4" src={getLink("images/arrow-left.svg")} alt="Next" />
  Previous
</a>
```

**After**:
```svelte
<a
  href={getLink(props.previousPage)}
  class="..."
>
  <img class="inline h-4" src={getLink("images/arrow-left.svg")} alt={$t('buttons.previous')} />
  {$t('buttons.previous')}
</a>
```

Do the same for the "Next" button.

### Step 7: Update Homepage

**File**: `src/routes/+page.svelte`

**Changes needed**:

1. Import translation function:
```javascript
import { t } from 'svelte-i18n';
```

2. Replace all hardcoded text:

**Before**:
```svelte
<h1 class="text-4xl font-extrabold text-gray-900">
  PyScript <span class="text-green-600">L</span>.<span class="text-blue-600">A</span>.<span class="text-yellow-500">B</span>
</h1>
<p class="text-lg text-gray-600">
  Python in the Browser. No Server Required.
</p>
```

**After**:
```svelte
<h1 class="text-4xl font-extrabold text-gray-900">
  {$t('home.title')}
</h1>
<p class="text-lg text-gray-600">
  {$t('home.subtitle')}
</p>
```

Continue this pattern for all text on the homepage.

### Step 8: Update Example Pages

For each example page in `src/routes/examples/`:

1. Import translation:
```javascript
import { t } from 'svelte-i18n';
```

2. Replace the `name` variable:

**Before**:
```javascript
export let name = 'HELLO WORLD';
```

**After**:
```javascript
$: name = $t('examples.hello.title');
```

3. Replace all hardcoded text with translation calls.

#### Example: Hello World Page

**File**: `src/routes/examples/basics/hello/+page.svelte`

**Key changes**:

```svelte
<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

<div class="prose max-w-none">
  <p class="mb-4">
    {$t('examples.hello.description')}
  </p>

  <div class="mb-6 rounded-lg bg-gray-100 p-4">
    <h3 class="mb-2 text-lg font-bold">{$t('examples.hello.keyFeatures.title')}</h3>
    <ul class="list-disc space-y-2 pl-5">
      <li>
        <strong>{$t('examples.hello.keyFeatures.zeroSetup')}</strong>
        {$t('examples.hello.keyFeatures.zeroSetupDesc')}
      </li>
      <!-- Continue for all list items -->
    </ul>
  </div>
</div>
```

### Step 9: Update SiteMapStore (Advanced)

**File**: `src/lib/stores/SiteMapStore.js`

**Option A: Static Approach (Simpler)**

Keep the SiteMap as-is and just translate the display of titles in components using translation keys based on page IDs.

**Option B: Dynamic Approach (Complete)**

Convert to a derived store that updates when locale changes:

```javascript
import { derived } from 'svelte/store';
import { _ } from 'svelte-i18n';
import { SiteMap, Page, PageProp } from "../SiteMap";
import { getLink } from "../utils.js";

export const SiteMapStore = derived(_, ($t) => {
  const pages = [
    new Page(
      "basics",
      $t('nav.basicExamples'),
      getLink("/examples/basics/hello"),
      [
        new PageProp("show", "all"),
        new PageProp("prev_page", getLink("/")),
        new PageProp("next_page", getLink("/examples/basics/repl")),
      ],
      [
        new Page(
          "hello-world",
          $t('nav.helloWorld'),
          getLink("/examples/basics/hello"),
          [/* props */]
        ),
        // ... more pages
      ]
    ),
    // ... more pages
  ];

  const siteMap = new SiteMap(pages);
  siteMap.setMainMenuTemplate("py-5 px-2 hover:text-yellow-500");
  siteMap.setMobileTemplate("block p-4 hover:text-white hover:bg-yellow-500");

  return siteMap;
}, null); // Initialize with null
```

**Important**: If using Option B, you need to handle the initial null value in components that use the store.

### Step 10: Testing Checklist

After implementation, test the following:

#### Functionality Tests
- [ ] Application loads without errors
- [ ] All pages render correctly in English
- [ ] Language switcher appears on desktop and mobile
- [ ] Clicking language switcher shows available languages
- [ ] Selecting a language changes the UI text
- [ ] Selected language persists after page refresh
- [ ] Selected language persists across navigation
- [ ] HTML lang attribute updates when language changes

#### Visual Tests
- [ ] No layout breaks with longer text (test with German)
- [ ] All buttons still fit properly
- [ ] Navigation menu doesn't overflow
- [ ] Mobile navigation works correctly
- [ ] Language switcher dropdown is properly positioned

#### Content Tests
- [ ] All navigation items are translated
- [ ] Homepage content is fully translated
- [ ] Example pages show translated content
- [ ] Button labels are translated
- [ ] Error messages are translated (if any appear)
- [ ] Visitor count shows correct format

#### Browser Tests
- [ ] Works in Chrome
- [ ] Works in Firefox
- [ ] Works in Safari
- [ ] Works in Edge
- [ ] Works on mobile devices

### Step 11: Adding New Languages

To add a new language:

1. Create translation file: `src/lib/i18n/locales/[locale].json`

2. Register the locale in `src/lib/i18n/index.js`:
```javascript
register('de', () => import('./locales/de.json'));
```

3. Add to AVAILABLE_LOCALES:
```javascript
export const AVAILABLE_LOCALES = {
  // ... existing
  de: { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
};
```

4. Test the new language thoroughly

### Step 12: Translation Workflow

#### For Developers

1. **Adding new strings**:
   - Add to `en.json` first
   - Use descriptive keys: `page.section.element`
   - Add comments in the JSON for context (if tool supports)

2. **Using strings**:
   ```svelte
   <p>{$t('key.name')}</p>
   ```

3. **With interpolation**:
   ```svelte
   <p>{$t('key.name', { values: { count: 5 } })}</p>
   ```

#### For Translators

1. Copy `en.json` to new locale file
2. Translate values, keep keys unchanged
3. Test interpolation placeholders (`{variable}`)
4. Consider text expansion (some languages are 30% longer)
5. Maintain HTML tags if present
6. Keep code examples untranslated

### Common Issues and Solutions

#### Issue 1: "Translation key not found"

**Symptom**: Console warning about missing translation

**Solution**: 
- Check spelling of translation key
- Ensure key exists in the translation file
- Check that locale file is registered in `index.js`

#### Issue 2: Text showing as `[object Object]`

**Symptom**: Component shows `[object Object]` instead of text

**Solution**:
- You're passing an object to $t instead of a string key
- Check the translation key is a string: `$t('key')` not `$t(objectVariable)`

#### Issue 3: Translations not updating when language changes

**Symptom**: UI doesn't refresh after changing language

**Solution**:
- Ensure you're using `$t()` (with $) not `t()`
- Check that component is subscribed to the locale store
- Verify the translation file was loaded (check Network tab)

#### Issue 4: Layout breaks with longer text

**Symptom**: Buttons overflow, text wraps oddly

**Solution**:
- Use flexbox with proper wrapping
- Test with German (typically longest)
- Add `overflow-hidden` and `text-ellipsis` where appropriate
- Consider responsive font sizes

#### Issue 5: Pluralization not working

**Symptom**: Always shows "1 items" instead of "1 item"

**Solution**:
```json
{
  "items": "{count, plural, =0 {no items} one {# item} other {# items}}"
}
```

Usage:
```svelte
{$t('items', { values: { count: itemCount } })}
```

### Performance Optimization

#### 1. Lazy Loading Translations

Already handled by dynamic imports in the register function.

#### 2. Preloading Next Locale

Add to language switcher:
```svelte
<button
  onmouseenter={() => {
    // Preload on hover
    import(`$lib/i18n/locales/${language.code}.json`);
  }}
>
```

#### 3. Bundle Size Analysis

Check bundle sizes:
```bash
npm run build
```

Each locale file adds ~10-15KB (depending on content).

### Maintenance

#### Monthly Tasks
- [ ] Check for untranslated strings
- [ ] Review translation quality
- [ ] Update translations with new content

#### Per Release
- [ ] Extract new strings to translation files
- [ ] Send to translators
- [ ] QA all locales
- [ ] Update documentation

### Migration Timeline

| Week | Tasks | Hours |
|------|-------|-------|
| 1 | Steps 1-4: Setup + Core Components | 6-8 |
| 2 | Steps 5-7: Navigation + Common Components | 6-8 |
| 3 | Step 8: Example Pages (Part 1) | 8-10 |
| 4 | Step 8: Example Pages (Part 2) + Step 9: SiteMap | 6-8 |
| 5 | Steps 10-11: Testing + Bug Fixes | 4-6 |
| **Total** | | **30-40 hours** |

### Rollout Strategy

#### Phase 1: Soft Launch (Week 1)
- Implement English only (refactoring)
- Test thoroughly
- Fix any issues

#### Phase 2: Beta Testing (Week 2)
- Add 1-2 additional languages
- Enable for beta users
- Collect feedback

#### Phase 3: Full Launch (Week 3)
- Add all planned languages
- Enable for all users
- Monitor for issues

### Success Metrics

Track these metrics post-implementation:
- Locale distribution of users
- Bounce rate per locale
- Time on site per locale
- Visitor count from non-English countries
- GitHub stars/forks from international community

## Conclusion

This migration guide provides a concrete, step-by-step path to implementing i18n in PyScript Lab. Follow the steps in order, test thoroughly at each stage, and don't hesitate to start with a smaller scope (English + one other language) before expanding to more locales.


