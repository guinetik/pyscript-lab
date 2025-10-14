# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyScript L.A.B is a collection of interactive examples demonstrating PyScript's capabilities for running Python directly in web browsers via WebAssembly. The project uses SvelteKit (Svelte 5 with runes), TailwindCSS v4, and PyScript 2025.2.1.

## Development Commands

### Essential Commands

**NEVER** run commands without explicitily being told to. Most of the time, user is running `npm run dev` on their system which is isolated from where you operate and it screws up node_modules and package_lock. If you absolutely need to run an npm command, ask first.

## Architecture

### PyScript Integration

**PyScript Configuration** (`src/app.html`):
- PyScript 2025.2.1 is loaded via CDN in the root HTML template
- Global packages are configured in `<py-config>` tag: bokeh, pandas, numpy, networkx, diagrams, scikit-learn, pillow, matplotlib, plotly
- Bokeh 3.6.2 and Plotly JavaScript libraries are loaded for visualization support
- A persistent Python console (using xterm.js) is available via the footer "Console" button

**RunPython Utility** (`src/lib/RunPython.js`):
- Factory function that creates controllers for executing Python code dynamically
- Returns an object with three methods:
  - `runScript(srcUrl, targetId, showCode)`: Loads and executes external Python files from `/static/python/`
  - `runCode(code, targetId, showCode)`: Executes inline Python code
  - `destroy(removeElements)`: Cleans up created `<script type="py">` elements
- Creates `<script type="py">` elements dynamically and appends them to the DOM
- **Critical for memory management**: Always call `destroy()` in Svelte's `onDestroy()` lifecycle hook to prevent memory leaks

### Component Architecture

**ExperimentCard Component** (`src/lib/components/ExperimentCard.svelte`):
- Standard layout wrapper for all example pages
- Split-pane design: interactive demo (left, 3/4 width) + documentation (right, 1/4 width)
- Two named slots:
  - `py_slot`: For the interactive PyScript demo area
  - `content_slot`: For documentation and explanation
- Footer contains `#script_gutter` div where Python output is rendered
- Navigation controls (Previous/Next) that link examples together
- Props: `{ previousPage: string, nextPage: string }`

**Example Page Pattern**:
All example pages follow this pattern:
1. Import `RunPython` and create instance in component script
2. Use `onMount()` to:
   - Expose JavaScript functions to `window` for Python to call
   - Initialize UI state and stores
   - Call `pyScriptRunner.runScript()` with path to Python file in `/static/python/`
3. Use `onDestroy()` to call `pyScriptRunner.destroy()`
4. Wrap content in `<ExperimentCard>` with navigation props
5. Python scripts in `/static/python/` can access DOM via `from pyscript import document`

### Code Organization Principles

**IMPORTANT: Follow these architectural guidelines strictly**

**1. Separation of Concerns - Use Controllers**

Keep Svelte components lean and focused on UI rendering. Extract complex logic to controller classes in `src/lib/controller/`:

- **Svelte Components** (`src/routes/` and `src/lib/components/`):
  - Handle only UI rendering, user interactions, and lifecycle management
  - Should be lightweight and readable
  - Import and use controllers for business logic

- **Controllers** (`src/lib/controller/`):
  - Contain all PyScript integration logic
  - Handle data transformations and business logic
  - Manage communication between Python and JavaScript
  - Examples: `DiagramCreatorController.js`, `SentimentAnalysisController.js`, `DiagramGalleryController.js`

**Example structure:**
```javascript
// src/lib/controller/MyFeatureController.js
export class MyFeatureController {
  constructor() {
    this.pyRunner = RunPython();
  }

  initialize() {
    this.setupPythonCallbacks();
    this.pyRunner.runScript('/python/my_feature.py');
  }

  setupPythonCallbacks() {
    window.handlePythonData = (data) => {
      // Transform and process data
      return this.processData(data);
    };
  }

  processData(data) {
    // Business logic here
  }

  destroy() {
    this.pyRunner.destroy();
  }
}
```

```svelte
<!-- src/routes/examples/my-feature/+page.svelte -->
<script>
  import { MyFeatureController } from '$lib/controller/MyFeatureController.js';
  import { onMount, onDestroy } from 'svelte';

  let controller = new MyFeatureController();

  onMount(() => controller.initialize());
  onDestroy(() => controller.destroy());
</script>
```

**2. Data-Only Communication: Avoid innerHTML from Python**

**Never use `innerHTML` or direct DOM manipulation from Python.** Python should only send data, not HTML.

**❌ Bad Pattern:**
```python
# Python manipulating DOM directly
from pyscript import document
document.querySelector("#result").innerHTML = "<div>Result: 42</div>"
```

**✅ Good Pattern:**
```python
# Python sending only data
from js import window
window.updateResult({"value": 42, "status": "success"})
```

```javascript
// JavaScript/Svelte handling rendering
window.updateResult = (data) => {
  resultStore.set(data);  // Let Svelte reactivity handle the DOM
};
```

**Benefits of data-only communication:**
- Maintains Svelte's reactivity system
- Prevents XSS vulnerabilities
- Easier to test and debug
- Clear separation between data and presentation
- Svelte components remain the single source of truth for UI

**Pattern to follow:**
1. Python computes/processes data
2. Python calls JavaScript function with data via `window.callbackName(data)`
3. JavaScript updates Svelte stores or component state
4. Svelte reactively updates the DOM

### State Management

**Svelte Stores Pattern**:
- Stores are used for reactive state between Python and JavaScript
- Example: `src/lib/stores/digitRecognitionStore.js` for ML example
- JavaScript exposes update functions on `window` object for Python to call
- **Important**: Convert Pyodide proxies to plain JavaScript objects to avoid destruction errors:
  ```javascript
  window.updateData = (data) => {
    const plainData = {
      value: data.value,
      array: Array.from(data.array || [])
    };
    store.set(plainData);
  };
  ```

### Navigation & Routing

**SiteMapStore** (`src/lib/stores/SiteMapStore.js`):
- Centralized navigation configuration using custom `SiteMap`, `Page`, and `PageProp` classes
- Defines all routes, page titles, URLs, and navigation relationships
- Each page has properties: `show` (all/mobile/none), `prev_page`, `next_page`
- Hierarchical structure with parent pages and sub-pages

**Base Path Handling** (`src/lib/utils.js`):
- `getLink(page)` function handles development vs production URLs
- In development: returns paths as-is (e.g., `/examples/hello`)
- In production: prepends `/python-ds` base path
- **Always use `getLink()` for internal links and asset paths**

### Python File Organization

Python scripts are organized in `/static/python/` by category:
- `/static/python/basic/`: Simple examples (date.py, fibo.py, snek.py)
- `/static/python/bokeh/`: Bokeh visualization scripts
- `/static/python/matplotlib/`: Matplotlib charts and maps
- `/static/python/diagrams/`: Architecture diagram generators
- `/static/python/ml/`: Machine learning examples
- `/static/python/interop.py`: JavaScript ↔ Python communication demo

**Python-JavaScript Interop Pattern**:
- **From Python**: Access browser globals via `window` and `document` from pyscript module
- **From JavaScript**: Python functions exposed to window are callable as `window.pythonFunctionName()`
- **Passing Data**: Use JSON-serializable data structures; avoid raw canvas ImageData

## Key Technical Notes

### PyScript Loading & Performance
- First load takes 5-10 seconds to download and initialize WebAssembly runtime
- Subsequent navigation is fast since PyScript is cached
- Heavy computations should show loading/progress indicators

### Memory Management
- **Critical**: Always call `pyScriptRunner.destroy()` in `onDestroy()` hooks
- Python script elements persist in DOM unless explicitly removed
- Each page navigation without cleanup adds memory overhead

### Python Package Configuration
- Packages are declared globally in `src/app.html` `<py-config>` section
- Adding new packages requires modifying this configuration
- Some packages may not be available or may have limitations in browser environment

### Canvas & Image Processing
- When passing canvas data to Python, use `canvas.toDataURL('image/png')` for base64 encoding
- Python can decode base64 images using PIL/Pillow
- For ML preprocessing, typical workflow: Canvas → Base64 → PIL Image → NumPy array → Model input

### Static Site Generation
- Uses `@sveltejs/adapter-static` for static site generation
- Build output is fully static (no server required)
- Base path `/python-ds` is configured for GitHub Pages hosting
- All routes must be pre-rendered at build time

## Adding New Examples

To add a new example page:

1. Create Svelte page in `src/routes/examples/{category}/{name}/+page.svelte`
2. Create Python script in `static/python/{category}/{name}.py`
3. Use the standard pattern:
   ```svelte
   <script>
     import ExperimentCard from '$lib/components/ExperimentCard.svelte';
     import RunPython from '$lib/RunPython.js';
     import { onMount, onDestroy } from 'svelte';

     let pyScriptRunner = RunPython();

     onMount(() => {
       pyScriptRunner.runScript('/python/{category}/{name}.py', 'script_gutter', false);
     });

     onDestroy(() => {
       if (pyScriptRunner) pyScriptRunner.destroy();
     });
   </script>

   <ExperimentCard props={{ previousPage: '/previous', nextPage: '/next' }}>
     <div slot="py_slot">
       <!-- Interactive demo here -->
     </div>
     <article slot="content_slot">
       <!-- Documentation here -->
     </article>
   </ExperimentCard>
   ```
4. Add page to navigation in `src/lib/stores/SiteMapStore.js`
5. Update previous/next page links in adjacent pages

## Browser Compatibility

Requires modern browsers with WebAssembly support:
- Chrome/Edge 90+
- Firefox 88+
- Safari 15+
