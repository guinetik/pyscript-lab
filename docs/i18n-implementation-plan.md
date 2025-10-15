# i18n Implementation Plan for PyScript Lab

## Executive Summary

This document outlines a comprehensive plan for implementing internationalization (i18n) in the PyScript Lab application. The strategy leverages `svelte-i18n` for SvelteKit integration and follows modern i18n best practices.

## Current State Analysis

### Application Architecture
- **Framework**: SvelteKit (Svelte 5 with runes)
- **Build**: Static site generation (`@sveltejs/adapter-static`)
- **Routing**: File-based routing (`src/routes/`)
- **Content**: Mix of static text in Svelte components and dynamic content

### Content to Translate

1. **Navigation** (`Nav.svelte`)
   - Menu items (Basic Examples, Matplotlib, Bokeh, Diagrams, Machine Learning)
   - Mobile navigation
   - External links

2. **Homepage** (`+page.svelte`)
   - Hero section (title, descriptions, CTAs)
   - Feature cards (6 sections with titles and descriptions)
   - Tech stack section

3. **Example Pages** (20 pages)
   - Page titles and headings
   - Instructions and descriptions
   - Button labels (Clear, Predict, Previous, Next, etc.)
   - Info boxes and tooltips
   - Documentation content

4. **Components**
   - `ExperimentCard.svelte` - Navigation button labels
   - Various ML components - Status messages, labels
   - Error messages and console outputs

5. **Site Map** (`SiteMapStore.js`)
   - Page titles and menu labels

## Recommended Approach

### 1. Library Selection: `svelte-i18n`

**Why `svelte-i18n`:**
- Native Svelte/SvelteKit support
- SSR and CSR compatibility
- Small bundle size (~3KB)
- Format.js integration for pluralization and date formatting
- Active maintenance and community support

**Alternatives considered:**
- `sveltekit-i18n` - More opinionated, less flexible
- `typesafe-i18n` - TypeScript-heavy, more complex setup
- Custom solution - Unnecessary overhead

### 2. Implementation Strategy

#### Phase 1: Foundation Setup (2-3 hours)

**1.1 Install Dependencies**
```bash
npm install svelte-i18n
```

**1.2 Project Structure**
```
src/
├── lib/
│   └── i18n/
│       ├── index.js          # i18n configuration and initialization
│       ├── locales/
│       │   ├── en.json       # English translations
│       │   ├── es.json       # Spanish translations (example)
│       │   └── pt.json       # Portuguese translations (example)
│       └── README.md         # Translation guidelines
```

**1.3 Configuration File** (`src/lib/i18n/index.js`)
```javascript
import { register, init, getLocaleFromNavigator } from 'svelte-i18n';

// Register locales
register('en', () => import('./locales/en.json'));
register('es', () => import('./locales/es.json'));
register('pt', () => import('./locales/pt.json'));

// Initialize i18n
export function initializeI18n() {
  init({
    fallbackLocale: 'en',
    initialLocale: getLocaleFromNavigator(),
  });
}
```

**1.4 Root Layout Integration** (`src/routes/+layout.svelte`)
```svelte
<script>
  import { initializeI18n } from '$lib/i18n';
  import { waitLocale } from 'svelte-i18n';
  import { onMount } from 'svelte';
  
  initializeI18n();
  
  // Wait for locale to load
  let ready = false;
  onMount(async () => {
    await waitLocale();
    ready = true;
  });
</script>

{#if ready}
  <slot />
{:else}
  <div class="flex items-center justify-center h-screen">
    <div class="text-xl">Loading...</div>
  </div>
{/if}
```

#### Phase 2: Core Components (4-5 hours)

**2.1 Navigation Component**
- Extract all text strings to translation keys
- Implement language switcher in navigation bar
- Support dropdown for multiple languages

**2.2 Homepage**
- Translate hero section
- Translate feature cards
- Translate tech stack section

**2.3 Shared Components**
- `ExperimentCard.svelte` - Button labels
- `PyExample.svelte` - Labels and titles
- Status messages and alerts

#### Phase 3: Example Pages (8-10 hours)

**3.1 Basic Examples**
- Hello World
- REPL
- Interoperability
- Advanced Interop

**3.2 Visualization Examples**
- Matplotlib pages (3 pages)
- Bokeh pages (4 pages)
- Diagrams pages (2 pages)

**3.3 Machine Learning Examples**
- Digit Recognition
- Sentiment Analysis
- Reinforcement Learning (2 pages)

#### Phase 4: SiteMap Integration (2-3 hours)

**4.1 Dynamic SiteMap**
- Refactor `SiteMapStore.js` to use translation keys
- Make page titles and labels dynamic
- Update navigation rendering logic

**4.2 URL Strategy**
Two approaches:
1. **Locale in path**: `/en/examples/hello`, `/es/examples/hello`
2. **Subdomain/cookie**: Keep current URLs, store locale in localStorage/cookie

**Recommendation**: Use localStorage/cookie approach to maintain simple URLs and avoid breaking existing links.

#### Phase 5: Language Switcher UI (2 hours)

**5.1 Component Design**
```svelte
<!-- LanguageSwitcher.svelte -->
<script>
  import { locale, locales } from 'svelte-i18n';
  
  const languages = {
    en: '🇺🇸 English',
    es: '🇪🇸 Español',
    pt: '🇧🇷 Português',
  };
</script>

<div class="relative group">
  <button class="flex items-center gap-2 px-3 py-2">
    {languages[$locale]}
  </button>
  <div class="dropdown">
    {#each $locales as loc}
      <button on:click={() => $locale = loc}>
        {languages[loc]}
      </button>
    {/each}
  </div>
</div>
```

**5.2 Integration Points**
- Desktop navigation bar
- Mobile menu
- Footer (optional)

#### Phase 6: Python Content (Special Consideration)

**Important**: Python code examples and outputs should generally NOT be translated, but labels around them should be.

**Strategy**:
- Translate: Button labels, instructions, error messages
- Don't translate: Python code, console output (unless specifically localized)
- Consider: Comments in Python files could be translated as separate files

#### Phase 7: Testing & QA (3-4 hours)

**7.1 Functionality Testing**
- All pages render in all languages
- Language switcher works correctly
- Locale persists across navigation
- No broken translations (missing keys)

**7.2 Visual Testing**
- Layout doesn't break with longer translations
- RTL support (if adding Arabic/Hebrew)
- Mobile responsiveness

**7.3 Performance Testing**
- Bundle size impact
- Initial load time
- Language switching speed

## Translation File Structure

### English (`en.json`) - Example Structure
```json
{
  "nav": {
    "home": "Home",
    "basicExamples": "Basic Examples",
    "matplotlib": "Matplotlib",
    "bokeh": "Bokeh",
    "diagrams": "Diagrams as Code",
    "machineLearning": "Machine Learning",
    "viewSource": "View Source",
    "visitors": "{count} Visitors"
  },
  "home": {
    "title": "PyScript L.A.B",
    "subtitle": "Python in the Browser. No Server Required.",
    "description": "Explore interactive examples demonstrating real-world Python applications running entirely in your browser using PyScript and modern web technologies.",
    "startExploring": "Start Exploring",
    "learnMore": "Learn More",
    "features": {
      "basic": {
        "title": "Basic Examples",
        "description": "Get started with PyScript fundamentals: Hello World, REPL environments, and Python-JavaScript interoperability.",
        "count": "{n} Examples"
      }
      // ... more features
    }
  },
  "examples": {
    "hello": {
      "title": "HELLO WORLD",
      "description": "PyScript allows you to run Python code directly in your web browser...",
      "keyFeatures": "Key Features:",
      "theExamples": "The Examples:",
      // ... more content
    }
    // ... more examples
  },
  "buttons": {
    "clear": "Clear",
    "predict": "Predict",
    "previous": "Previous",
    "next": "Next",
    "openConsole": "🖥️ Open Console to see script output"
  },
  "ml": {
    "digitRecognition": {
      "title": "Machine Learning - Digit Recognition",
      "drawNumber": "Draw a Number",
      "instruction": "Draw a digit (0-9) on the canvas and click "Predict" to see what the machine learning model thinks you drew!",
      // ... more content
    }
  }
}
```

### Namespace Strategy

Organize translations by:
1. **Component/Page** - Group by logical sections
2. **Shared** - Common strings (buttons, errors, etc.)
3. **Content** - Long-form documentation content

## Implementation Timeline

| Phase | Description | Time Estimate | Priority |
|-------|-------------|---------------|----------|
| 1 | Foundation Setup | 2-3 hours | Critical |
| 2 | Core Components | 4-5 hours | High |
| 3 | Example Pages | 8-10 hours | High |
| 4 | SiteMap Integration | 2-3 hours | Medium |
| 5 | Language Switcher UI | 2 hours | High |
| 6 | Python Content | 1-2 hours | Low |
| 7 | Testing & QA | 3-4 hours | Critical |
| **Total** | | **22-29 hours** | |

## Best Practices & Guidelines

### 1. Translation Keys
- Use dot notation: `nav.home`, `buttons.clear`
- Descriptive, not positional: `hero.title` not `page1.text1`
- Group by context, not by page location

### 2. Interpolation
```javascript
// Use named parameters
$t('nav.visitors', { values: { count: 42 } })
// Results in: "42 Visitors"
```

### 3. Pluralization
```json
{
  "examples.count": "{n, plural, =0 {No examples} one {# example} other {# examples}}"
}
```

### 4. Date/Number Formatting
```javascript
import { date, number } from 'svelte-i18n';

$date(new Date(), { format: 'short' })
$number(1234.56, { style: 'currency', currency: 'USD' })
```

### 5. Fallback Strategy
- Always provide English as fallback
- Mark missing translations in dev mode
- Don't break UI if translation is missing

## Accessibility Considerations

1. **Language Attribute**: Update `<html lang="...">` dynamically
2. **Screen Readers**: Ensure language switcher is properly labeled
3. **Keyboard Navigation**: Language switcher should be keyboard accessible
4. **ARIA Labels**: Translate ARIA labels and alt text

## SEO Considerations

For static site generation:
1. **Meta Tags**: Translate page titles and descriptions
2. **Structured Data**: Update JSON-LD in appropriate language
3. **Hreflang**: Add language alternates (if using path-based locales)
4. **sitemap.xml**: Generate per-locale or include all locales

## Performance Optimization

1. **Code Splitting**: Load only active locale
2. **Lazy Loading**: Load translations on demand for large pages
3. **Caching**: Cache locale preference and translations
4. **Preloading**: Preload next locale on hover

## Maintenance Plan

1. **Translation Workflow**:
   - Developer adds English keys
   - Translation service (e.g., Crowdin, Lokalise) for other languages
   - Pull requests for translation updates

2. **Validation**:
   - Script to detect missing keys
   - CI/CD integration to prevent deploys with incomplete translations

3. **Documentation**:
   - Translation guidelines for contributors
   - Key naming conventions
   - Context for translators (screenshots, descriptions)

## Budget Estimates

### Development Time
- Implementation: 22-29 hours
- Testing: 3-4 hours
- **Total Development**: ~25-33 hours

### Translation Costs (per language)
- Professional translation: ~$0.10-0.15 per word
- Estimated word count: ~3,000-4,000 words
- **Cost per language**: $300-600

### Tools (Optional)
- Lokalise Pro: $120/month
- Crowdin Pro: $80/month
- OR use free tier for open source projects

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Layout breaking with long translations | High | Design with 30% text expansion buffer |
| Missing translations | Medium | Comprehensive fallback strategy |
| Performance degradation | Low | Lazy loading and code splitting |
| Maintenance overhead | Medium | Automated validation tools |
| Python content complexity | Low | Clear guidelines on what to translate |

## Recommended Initial Languages

Based on Python community and web usage:

1. **English (en)** - Base language ✅
2. **Spanish (es)** - 460M speakers, strong Python community
3. **Portuguese (pt)** - 220M speakers, growing tech community in Brazil
4. **Chinese Simplified (zh-CN)** - Huge Python user base
5. **German (de)** - Strong engineering community

## Next Steps

1. **Approval**: Review and approve this plan
2. **Setup**: Install dependencies and create base structure
3. **Pilot**: Implement Phase 1-2 for homepage and navigation
4. **Review**: Evaluate pilot before full implementation
5. **Scale**: Complete remaining phases
6. **Launch**: Deploy with initial language support

## Resources

- [svelte-i18n Documentation](https://github.com/kaisermann/svelte-i18n)
- [Format.js Internationalization](https://formatjs.io/)
- [SvelteKit i18n Guide](https://kit.svelte.dev/docs/internationalization)
- [W3C i18n Best Practices](https://www.w3.org/International/techniques/authoring-html)

## Conclusion

This implementation plan provides a structured approach to adding i18n support to PyScript Lab. The use of `svelte-i18n` ensures compatibility with Svelte 5 and SvelteKit, while the phased approach allows for incremental development and testing. The estimated timeline of 25-33 hours makes this a manageable enhancement that will significantly increase the application's reach and accessibility to non-English speakers.

