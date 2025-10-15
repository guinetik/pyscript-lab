# i18n Code Examples

This document provides concrete code examples showing how to implement i18n in PyScript Lab.

## Table of Contents
1. [Setup and Configuration](#setup-and-configuration)
2. [Translation Files](#translation-files)
3. [Component Examples](#component-examples)
4. [Advanced Usage](#advanced-usage)

## Setup and Configuration

### 1. Install Dependencies

```bash
npm install svelte-i18n
```

### 2. i18n Configuration (`src/lib/i18n/index.js`)

```javascript
/**
 * Internationalization configuration for PyScript Lab.
 * Initializes svelte-i18n with locale detection and fallback handling.
 * @module i18n
 */
import { register, init, getLocaleFromNavigator, locale } from 'svelte-i18n';

// Register locale loaders
register('en', () => import('./locales/en.json'));
register('es', () => import('./locales/es.json'));
register('pt', () => import('./locales/pt.json'));
register('zh', () => import('./locales/zh.json'));
register('de', () => import('./locales/de.json'));

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
    // Update HTML lang attribute for accessibility
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
  zh: { code: 'zh', name: '中文', flag: '🇨🇳' },
  de: { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
};
```

### 3. Root Layout Update (`src/routes/+layout.svelte`)

```svelte
<script>
  import '../app.css';
  import Nav from '../lib/components/Nav.svelte';
  import { initializeI18n } from '$lib/i18n';
  import { isLoading } from 'svelte-i18n';
  import { onMount } from 'svelte';

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

## Translation Files

### English (`src/lib/i18n/locales/en.json`)

```json
{
  "nav": {
    "home": "Home",
    "basicExamples": "Basic Examples",
    "matplotlib": "Matplotlib",
    "bokeh": "Bokeh",
    "diagrams": "Diagrams as Code",
    "machineLearning": "Machine Learning",
    "github": "Github",
    "viewSource": "View Source",
    "visitors": "{count} Visitors",
    "toggleMenu": "Toggle menu",
    "closeMenu": "Close menu"
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
      },
      "bokeh": {
        "title": "Bokeh Visualizations",
        "description": "Interactive data visualizations with Bokeh: Pandas integration, network graphs, and community detection algorithms.",
        "count": "3 Examples"
      },
      "diagrams": {
        "title": "Diagrams as Code",
        "description": "Generate cloud architecture diagrams programmatically. Version-controlled infrastructure visualization.",
        "count": "5 Examples"
      },
      "matplotlib": {
        "title": "Matplotlib & Maps",
        "description": "Data visualization with matplotlib and interactive world maps. COVID-19 data analysis and geographic visualization.",
        "count": "3 Examples"
      },
      "ml": {
        "title": "Machine Learning",
        "description": "Browser-based ML with scikit-learn: Handwritten digit recognition, sentiment analysis, and reinforcement learning with NES games.",
        "count": "3 Examples"
      },
      "about": {
        "title": "About This Lab",
        "description": "Exploring PyScript's capabilities and demonstrating how Python integrates with modern JavaScript frameworks like Svelte.",
        "footer": "All code runs in your browser. No backend servers, no API calls. Just Python + WebAssembly."
      }
    },
    "techStack": {
      "title": "Technology Stack",
      "pyscript": {
        "title": "PyScript",
        "subtitle": "Python in Browser"
      },
      "dataScience": {
        "title": "Data Science",
        "subtitle": "Pandas, NumPy, Plotly"
      },
      "svelte": {
        "title": "Svelte 5",
        "subtitle": "Reactive Framework"
      },
      "webassembly": {
        "title": "WebAssembly",
        "subtitle": "Native Performance"
      }
    }
  },
  "buttons": {
    "clear": "Clear",
    "predict": "Predict",
    "previous": "Previous",
    "next": "Next",
    "openConsole": "🖥️ Open Console to see script output",
    "showTrainingExamples": "📚 Show Training Examples",
    "hideTrainingExamples": "Hide Training Examples",
    "viewSource": "View source"
  },
  "examples": {
    "hello": {
      "title": "HELLO WORLD",
      "example1": "Example 1",
      "example2": "Example 2",
      "example3": "Example 3",
      "example4": "Example 4",
      "printHelloWorld": "Print hello world:",
      "currentDateTime": "Current date and time, as computed by Python:",
      "fibonacci": "Fibonacci sequence, computed by Python:",
      "snakeTraversal": "Snake traversal, computed by Python:",
      "description": "PyScript allows you to run Python code directly in your web browser without any server-side processing. These examples demonstrate Python's capabilities, from basic \"Hello World\" output to date handling, Fibonacci sequences, and matrix traversals—all running entirely in your browser.",
      "keyFeatures": {
        "title": "Key Features:",
        "zeroSetup": "Zero Server Setup:",
        "zeroSetupDesc": "Python runs entirely in the browser using WebAssembly",
        "stdLib": "Standard Library Access:",
        "stdLibDesc": "Use familiar Python modules like {modules} and more",
        "simpleIntegration": "Simple Integration:",
        "simpleIntegrationDesc": "Add Python with just a {tag} tag",
        "externalScripts": "External Scripts:",
        "externalScriptsDesc": "Load Python code from files using the {attr} attribute",
        "consoleOutput": "Console Output:",
        "consoleOutputDesc": "View results in the browser console or write to the DOM"
      },
      "theExamples": {
        "title": "The Examples:",
        "example1": "Classic \"Hello World\" - The simplest PyScript program",
        "example2": "Current date/time - Demonstrates external Python scripts and datetime module",
        "example3": "Fibonacci sequence - Shows algorithmic computation and list comprehension",
        "example4": "Snake traversal - Matrix manipulation and DOM manipulation from Python"
      },
      "gettingStarted": {
        "title": "Getting Started:",
        "description": "The basic pattern for running Python in the browser is simple:",
        "footer": "Click the \"🖥️ Open Console\" button above to see the output of these Python scripts!"
      }
    },
    "ml": {
      "digitRecognition": {
        "title": "Machine Learning - Digit Recognition",
        "heading": "Draw a Number",
        "instruction": "Draw a digit (0-9) on the canvas and click \"Predict\" to see what the machine learning model thinks you drew!",
        "howItWorks": {
          "title": "How it works:",
          "point1": "The model is trained on scikit-learn's digits dataset (1,797 samples of 8×8 images)",
          "point2": "When you click Predict, your drawing is converted to base64",
          "point3": "Python receives the image, preprocesses it to 8×8 grayscale with adaptive thresholding",
          "point4": "A {algorithm} classifier predicts the digit using 5 neighbors",
          "point5": "{feature} gives more importance to closer neighbors for better accuracy",
          "point6": "{feature}: If the prediction is wrong, you can correct it and retrain the model live!",
          "point7": "All processing happens in your browser using PyScript!"
        },
        "activeLearning": {
          "title": "💡 Active Learning with Positive & Negative Feedback",
          "description": "This model learns from {bold} correct and incorrect predictions! After each prediction, you can:",
          "clickYes": "Click YES if correct → Reinforces the model's understanding of your drawing style",
          "clickNo": "Click NO if wrong → Lets you correct it and retrain with the right label",
          "footer": "The more feedback you give (positive or negative), the better it gets at recognizing {emphasis} handwriting!"
        },
        "architecture": {
          "title": "🏗️ Architecture",
          "description": "This example demonstrates proper separation of concerns with event-driven initialization:",
          "pyScriptManager": "Event-driven lifecycle management (no polling!)",
          "python": "Pure ML logic, signals ready when initialized, sends only data via callbacks",
          "controller": "Manages communication layer between Python and UI",
          "svelteComponents": "Pure UI rendering with reactive state"
        }
      }
    }
  },
  "status": {
    "ready": "Ready",
    "processing": "Processing...",
    "error": "Error",
    "loading": "Loading...",
    "success": "Success!",
    "drawDigit": "Draw a digit and click Predict",
    "reinforced": "✓ Feedback recorded! Model reinforced.",
    "retrained": "✓ Model retrained with correction!",
    "reset": "Canvas cleared"
  },
  "errors": {
    "pythonNotReady": "Python is not ready yet. Please wait...",
    "predictionFailed": "Prediction failed. Please try again.",
    "invalidInput": "Invalid input. Please draw a clear digit.",
    "loadingFailed": "Failed to load the module. Please refresh the page."
  }
}
```

### Spanish (`src/lib/i18n/locales/es.json`)

```json
{
  "nav": {
    "home": "Inicio",
    "basicExamples": "Ejemplos Básicos",
    "matplotlib": "Matplotlib",
    "bokeh": "Bokeh",
    "diagrams": "Diagramas como Código",
    "machineLearning": "Aprendizaje Automático",
    "github": "Github",
    "viewSource": "Ver Código",
    "visitors": "{count} Visitantes",
    "toggleMenu": "Abrir menú",
    "closeMenu": "Cerrar menú"
  },
  "home": {
    "title": "PyScript L.A.B",
    "subtitle": "Python en el Navegador. Sin Servidor Requerido.",
    "description": "Explora ejemplos interactivos que demuestran aplicaciones Python del mundo real ejecutándose completamente en tu navegador usando PyScript y tecnologías web modernas.",
    "startExploring": "Comenzar a Explorar",
    "learnMore": "Aprender Más"
  },
  "buttons": {
    "clear": "Limpiar",
    "predict": "Predecir",
    "previous": "Anterior",
    "next": "Siguiente",
    "openConsole": "🖥️ Abrir Consola para ver la salida",
    "showTrainingExamples": "📚 Mostrar Ejemplos de Entrenamiento",
    "hideTrainingExamples": "Ocultar Ejemplos",
    "viewSource": "Ver código fuente"
  }
}
```

## Component Examples

### 1. Language Switcher Component (`src/lib/components/LanguageSwitcher.svelte`)

```svelte
<script>
  /**
   * Language switcher dropdown component.
   * Allows users to change the application locale and persists the selection.
   */
  import { locale, locales } from 'svelte-i18n';
  import { AVAILABLE_LOCALES, changeLocale } from '$lib/i18n';

  /** @type {boolean} */
  let isOpen = $state(false);

  /**
   * Toggle dropdown visibility
   * @returns {void}
   */
  function toggleDropdown() {
    isOpen = !isOpen;
  }

  /**
   * Close dropdown
   * @returns {void}
   */
  function closeDropdown() {
    isOpen = false;
  }

  /**
   * Handle locale selection
   * @param {string} newLocale - The locale code to switch to
   * @returns {void}
   */
  function selectLocale(newLocale) {
    changeLocale(newLocale);
    closeDropdown();
  }

  /** @type {string} */
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

<!-- Close dropdown when clicking outside -->
{#if isOpen}
  <button
    class="fixed inset-0 z-40"
    onclick={closeDropdown}
    aria-label="Close dropdown"
    tabindex="-1"
  ></button>
{/if}
```

### 2. Updated Navigation Component (`src/lib/components/Nav.svelte`)

```svelte
<script>
  import { getLink } from '../utils';
  import SiteMapStore from '../stores/SiteMapStore';
  import SiteMapLink from './SiteMapLink.svelte';
  import LanguageSwitcher from './LanguageSwitcher.svelte';
  import { page } from '$app/stores';
  import { beforeUpdate } from 'svelte';
  import { t } from 'svelte-i18n';

  let siteMap = null;
  let mobileLinks = [];
  let mainLinks = [];
  let visits = 0;
  let toggleBurgerMenu = false;

  SiteMapStore.subscribe((s) => {
    siteMap = s;
    mainLinks = siteMap.getMainLinks();
    mobileLinks = siteMap.getMobileLinks();
  });

  function syncVisits() {
    visits = window.visits;
  }

  beforeUpdate(syncVisits);

  function toggleMenu() {
    toggleBurgerMenu = !toggleBurgerMenu;
  }

  function closeMenu() {
    toggleBurgerMenu = false;
  }

  export let activePage = '';
  $: currentPath = activePage || $page.url.pathname;
</script>

<nav class="bg-gray-100">
  <div class="mx-auto max-w-screen-2xl px-4">
    <div class="flex justify-between">
      <div class="flex space-x-2">
        <div>
          <a
            href={getLink('/')}
            class="flex items-center px-2 py-5 text-gray-700 hover:text-gray-900"
          >
            <img src={getLink('images/python.svg')} alt="PyScript L.A.B" />
            <span class="font-bold">
              PyScript <span class="text-green-600">L</span>.<span class="text-blue-600">A</span>.<span class="text-yellow-500">B</span>
            </span>
          </a>
        </div>
        <div class="hidden items-center space-x-1 md:flex">
          {#each mainLinks as link}
            {#if link.page.hasChildren()}
              <div class="relative group">
                <button
                  class="py-5 px-2 hover:text-yellow-500 flex items-center gap-1 {currentPath.startsWith(link.page.url) ? 'text-yellow-500 font-bold' : 'text-gray-700'}"
                >
                  {$t(`nav.${link.page.id}`)}
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                  </svg>
                </button>
                <div class="absolute left-0 mt-0 w-56 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div class="py-1">
                    {#each link.page.children as child}
                      <a
                        href={child.url}
                        class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-yellow-500 {currentPath === child.url ? 'bg-yellow-50 text-yellow-500 font-bold' : ''}"
                      >
                        {$t(`nav.${child.id}`)}
                      </a>
                    {/each}
                  </div>
                </div>
              </div>
            {:else}
              <SiteMapLink
                template={link.template}
                page={link.page}
                active={currentPath}
                activeClass="main_menu_active"
              />
            {/if}
          {/each}
        </div>
      </div>
      <div class="hidden items-center space-x-3 md:flex">
        <!-- Language Switcher -->
        <LanguageSwitcher />
        
        <a href="https://github.com/guinetik/python-ds">
          <img
            src="https://img.shields.io/badge/-{$t('nav.viewSource')}-gray?style=flat-square&logo=github&logoColor=white&link=https://github.com/guinetik"
            alt={$t('nav.viewSource')}
          />
        </a>
        <a href="https://guinetik.github.io/python-ds/">
          <img
            src={`https://img.shields.io/static/v1?label=&message=${$t('nav.visitors', { values: { count: visits } })}&color=blueviolet&style=flat-square`}
            alt={$t('nav.visitors', { values: { count: visits } })}
          />
        </a>
        <a href="https://linkedin.com/in/guinetik">
          <img
            src="https://img.shields.io/badge/-LinkedIn-blue?style=flat-square&logo=Linkedin&logoColor=white&link=https://www.linkedin.com/in/guinetik/"
            alt="Linkedin"
          />
        </a>
      </div>
      <div class="flex items-center justify-between md:hidden">
        <button
          class="h-6 w-6"
          onclick={toggleMenu}
          aria-label={$t('nav.toggleMenu')}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            class="h-6 w-6"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>

  <!-- Mobile menu -->
  <nav
    id="mobile-navigation"
    class="{toggleBurgerMenu ? 'visible opacity-100' : 'invisible opacity-0'} fixed top-0 right-0 bottom-0 left-0 z-10 backdrop-blur-sm transition-all duration-500"
  >
    <ul
      class="{toggleBurgerMenu ? 'translate-x-0' : 'translate-x-full'} absolute top-0 right-0 bottom-0 z-10 bg-white drop-shadow-2xl transition-all duration-500"
    >
      <div class="border-b border-inherit p-4">
        <LanguageSwitcher />
      </div>
      {#each mobileLinks as link}
        <li class="border-b border-inherit">
          {#if link.page.hasChildren()}
            <div class="block p-4 text-gray-700 font-bold">{$t(`nav.${link.page.id}`)}</div>
            {#each link.page.children as child}
              <a
                href={child.url}
                onclick={closeMenu}
                class="block pl-8 p-3 text-sm hover:text-white hover:bg-yellow-500 {currentPath === child.url ? 'bg-yellow-50 text-yellow-500 font-bold' : ''}"
              >
                {$t(`nav.${child.id}`)}
              </a>
            {/each}
          {:else}
            <SiteMapLink
              onclick={closeMenu}
              template={link.template}
              page={link.page}
              active={currentPath}
              activeClass="mobile_menu_active"
            />
          {/if}
        </li>
      {/each}
    </ul>

    <button
      aria-label={$t('nav.closeMenu')}
      class="absolute top-0 right-0 bottom-0 left-0 {toggleBurgerMenu ? 'opacity-100' : 'opacity-0'}"
      onclick={closeMenu}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="absolute top-2 left-2 h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
    </button>
  </nav>
</nav>
```

### 3. Updated ExperimentCard Component

```svelte
<script>
  import { getLink } from "../utils.js";
  import { t } from 'svelte-i18n';

  export let props;
</script>

<main class="w-full h-[calc(100%-120px)]">
  <div class="py-10 w-full flex items-center justify-center h-full">
    <div class="bg-white rounded-lg shadow-2xl overflow-hidden w-10/12">
      <div class="md:flex">
        <section class="bg-slate-300 lg:w-3/4 md:flex-grow md:w-full min-h-[380px] md:rounded-l-lg">
          <slot name="py_slot" />
        </section>
        <section
          class="p-4 space-y-3 md:w-1/2 lg:w-4/12 border-t border-slate-900 md:border-l md:rounded-r-lg"
        >
          <slot name="content_slot" />
          <div class="flex">
            <a
              href={getLink(props.previousPage)}
              class="text-xs ml-0 py-2 px-3 bg-blue-400 hover:bg-slate-300 text-slate-900 hover:text-slate-800 rounded transition duration-300"
            >
              <img
                class="inline h-4"
                src={getLink("images/arrow-left.svg")}
                alt={$t('buttons.previous')}
              />
              {$t('buttons.previous')}
            </a>
            <a
              href={getLink(props.nextPage)}
              class="text-xs ml-auto py-2 px-3 bg-yellow-400 hover:bg-slate-300 text-slate-900 hover:text-slate-800 rounded transition duration-300"
            >
              {$t('buttons.next')}
              <img
                class="inline h-4"
                src={getLink("images/arrow-next.svg")}
                alt={$t('buttons.next')}
              />
            </a>
          </div>
        </section>
      </div>
      <footer class="py-3 px-6 bg-slate-800 text-xs text-white font-mono">
        <div id="script_gutter"></div>
      </footer>
    </div>
  </div>
</main>
```

### 4. Updated Homepage (`src/routes/+page.svelte`)

```svelte
<script>
  import { base } from '$app/paths';
  import { t } from 'svelte-i18n';
</script>

<main class="w-full">
  <div class="flex items-center justify-center py-10 px-4">
    <div class="max-w-7xl w-full space-y-8">
      <!-- Hero Section -->
      <div class="overflow-hidden rounded-lg bg-white shadow-2xl">
        <div class="md:flex">
          <img
            class="w-full rounded-lg object-cover object-center p-1 md:w-1/2"
            src="{base}/images/pyscript.png"
            alt="PyScript"
          />
          <div class="space-y-4 border-slate-900 p-8 sm:border-t md:border-l">
            <h1 class="text-4xl font-extrabold text-gray-900">
              {$t('home.title')}
            </h1>
            <p class="text-lg text-gray-600">
              {$t('home.subtitle')}
            </p>
            <p class="text-gray-700">
              {$t('home.description')}
            </p>
            <div class="flex gap-4 pt-4">
              <a
                href="{base}/examples/basics/hello"
                class="rounded-lg bg-blue-600 px-6 py-3 text-white font-semibold hover:bg-blue-700 transition-colors"
              >
                {$t('home.startExploring')}
              </a>
              <a
                href="https://pyscript.net/"
                target="_blank"
                class="rounded-lg border-2 border-blue-600 px-6 py-3 text-blue-600 font-semibold hover:bg-blue-50 transition-colors"
              >
                {$t('home.learnMore')}
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- Features Grid -->
      <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <!-- Basic Examples -->
        <a href="{base}/examples/basics/hello" class="group block h-full">
          <div class="h-full flex flex-col rounded-lg bg-white p-6 shadow-lg hover:shadow-xl transition-shadow border-2 border-transparent hover:border-blue-500">
            <div class="text-4xl mb-4">🐍</div>
            <h3 class="text-xl font-bold mb-2 text-gray-900 group-hover:text-blue-600">
              {$t('home.features.basic.title')}
            </h3>
            <p class="text-gray-600 text-sm mb-4 flex-grow">
              {$t('home.features.basic.description')}
            </p>
            <div class="text-blue-600 font-semibold text-sm">
              {$t('home.features.basic.count', { values: { n: 3 } })} →
            </div>
          </div>
        </a>

        <!-- More feature cards... -->
      </div>

      <!-- Tech Stack -->
      <div class="rounded-lg bg-white p-8 shadow-lg">
        <h2 class="text-2xl font-bold mb-6 text-gray-900">{$t('home.techStack.title')}</h2>
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center text-2xl">🐍</div>
            <div>
              <div class="font-semibold text-gray-900">{$t('home.techStack.pyscript.title')}</div>
              <div class="text-sm text-gray-600">{$t('home.techStack.pyscript.subtitle')}</div>
            </div>
          </div>
          <!-- More tech stack items... -->
        </div>
      </div>
    </div>
  </div>
</main>
```

## Advanced Usage

### 1. Formatting Numbers and Dates

```svelte
<script>
  import { t, number, date, time } from 'svelte-i18n';
  
  let visitCount = 12345;
  let lastUpdated = new Date();
</script>

<!-- Number formatting -->
<p>{$number(visitCount)}</p>
<!-- Output: "12,345" (en) or "12.345" (de) -->

<!-- Currency formatting -->
<p>{$number(99.99, { style: 'currency', currency: 'USD' })}</p>
<!-- Output: "$99.99" -->

<!-- Date formatting -->
<p>{$date(lastUpdated, { format: 'short' })}</p>
<!-- Output: "1/15/25" (en) or "15.1.25" (de) -->

<!-- Time formatting -->
<p>{$time(lastUpdated, { format: 'short' })}</p>
<!-- Output: "3:30 PM" (en) or "15:30" (de) -->
```

### 2. Pluralization

```json
{
  "examples.count": "{n, plural, =0 {No examples} one {# example} other {# examples}}"
}
```

```svelte
<script>
  import { t } from 'svelte-i18n';
  let count = 5;
</script>

<p>{$t('examples.count', { values: { n: count } })}</p>
<!-- Output: "5 examples" -->
```

### 3. Dynamic SiteMap with Translations

```javascript
// src/lib/stores/SiteMapStore.js
import { derived } from 'svelte/store';
import { _ } from 'svelte-i18n';
import { SiteMap, Page, PageProp } from "../SiteMap";
import { getLink } from "../utils.js";

// Create a derived store that updates when locale changes
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
          $t('examples.hello.title'),
          getLink("/examples/basics/hello"),
          [
            new PageProp("show", "none"),
            new PageProp("prev_page", getLink("/")),
            new PageProp("next_page", getLink("/examples/basics/repl")),
          ]
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
});

export default SiteMapStore;
```

### 4. Loading States and Error Handling

```svelte
<script>
  import { isLoading } from 'svelte-i18n';
  import { t } from 'svelte-i18n';
  
  let error = null;
  
  async function loadData() {
    try {
      // your async operation
    } catch (e) {
      error = $t('errors.loadingFailed');
    }
  }
</script>

{#if $isLoading}
  <div class="loading">{$t('status.loading')}</div>
{:else if error}
  <div class="error">{error}</div>
{:else}
  <!-- Your content -->
{/if}
```

### 5. Conditional Content Based on Locale

```svelte
<script>
  import { locale } from 'svelte-i18n';
</script>

{#if $locale === 'en'}
  <p>This content is only for English speakers.</p>
{:else if $locale === 'es'}
  <p>Este contenido es solo para hispanohablantes.</p>
{/if}

<!-- Or use a more elegant approach with translations -->
<p>{$t('locale-specific.content')}</p>
```

## Testing i18n

### Unit Test Example

```javascript
// tests/i18n.test.js
import { render } from '@testing-library/svelte';
import { init, locale, _ } from 'svelte-i18n';
import Component from './YourComponent.svelte';

describe('i18n', () => {
  beforeEach(() => {
    init({
      fallbackLocale: 'en',
      initialLocale: 'en',
    });
  });

  test('renders English text', async () => {
    locale.set('en');
    const { getByText } = render(Component);
    expect(getByText('Hello World')).toBeInTheDocument();
  });

  test('renders Spanish text', async () => {
    locale.set('es');
    const { getByText } = render(Component);
    expect(getByText('Hola Mundo')).toBeInTheDocument();
  });
});
```

## Best Practices Summary

1. **Always provide fallback**: Set `fallbackLocale: 'en'`
2. **Use descriptive keys**: `nav.home` not `n1`
3. **Group by context**: Organize translations by feature/component
4. **Interpolate with named parameters**: `{name}` not `{0}`
5. **Handle plurals properly**: Use Format.js plural syntax
6. **Test all locales**: Ensure nothing breaks with longer text
7. **Persist locale preference**: Use localStorage
8. **Update HTML lang**: For accessibility
9. **Lazy load translations**: Don't bundle all locales upfront
10. **Document translation keys**: Help translators understand context


