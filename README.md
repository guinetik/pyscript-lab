# PyScript L.A.B

> **L**earning **A**nd **B**uilding with Python in the Browser

A collection of interactive examples demonstrating PyScript's capabilities for running Python directly in the browser, built with modern web technologies.

## Motivation

PyScript enables Python to run natively in web browsers via WebAssembly, opening up new possibilities for:

- **Educational Tools**: Interactive Python tutorials and demonstrations without server setup
- **Data Science Visualization**: Client-side data analysis and visualization with familiar Python libraries
- **Rapid Prototyping**: Quick proof-of-concepts combining Python's ecosystem with web UIs
- **Offline-First Applications**: Python-powered apps that work without network connectivity

This project explores PyScript's capabilities through practical examples, from simple "Hello World" to complex machine learning applications with active learning.

## Architecture

### Tech Stack

- **Frontend**: [SvelteKit](https://kit.svelte.dev/) (Svelte 5 with runes)
- **Styling**: [TailwindCSS v4](https://tailwindcss.com/)
- **Python Runtime**: [PyScript 2025.2.1](https://pyscript.net/)
- **Visualization**: [Bokeh 3.6.2](https://bokeh.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)

### Project Structure

```
pyscript-lab/
├── src/
│   ├── lib/
│   │   ├── RunPython.js          # Utility for executing Python code
│   │   ├── ExperimentCard.svelte # Reusable layout component
│   │   └── SiteMapStore.js       # Navigation configuration
│   ├── routes/
│   │   └── examples/             # Example pages
│   │       ├── hello/
│   │       ├── repl/
│   │       ├── interop/
│   │       ├── bokeh/
│   │       ├── diagrams/
│   │       └── ml/
│   └── app.html                  # Root template with PyScript setup
├── static/
│   └── python/                   # Python scripts for examples
└── package.json

```

### Key Components

**RunPython Utility** (`src/lib/RunPython.js`)
- Dynamically creates `<script type="py">` elements
- Manages script lifecycle (creation, execution, cleanup)
- Supports both external scripts and inline code
- Enables component-scoped Python execution

**Experiment Card** (`src/lib/ExperimentCard.svelte`)
- Standardized layout for examples
- Split view: interactive demo (left) + documentation (right)
- Console output footer for debugging
- Navigation between examples

**Python Console** (`src/app.html`)
- Draggable, resizable modal dialog
- Interactive Python REPL using xterm.js
- Persistent across page navigation
- Clear and close functionality

## Examples Overview

### 1. Hello World
**Path**: `/examples/hello`

The classic starter - displays current date/time using Python's `datetime` module. Demonstrates basic PyScript integration and DOM manipulation.

### 2. R.E.P.L
**Path**: `/examples/repl`

Interactive Python REPL with syntax highlighting and code execution. Shows how to capture user input and execute arbitrary Python code in the browser.

### 3. Interoperability in Python
**Path**: `/examples/interop`

JavaScript ↔ Python communication example. Demonstrates:
- Calling Python functions from JavaScript
- Passing parameters between languages
- Generating dynamic visualizations based on user input

### 4. Bokeh Visualizations
**Path**: `/examples/bokeh/*`

Four progressive examples showcasing data visualization:

#### a) **Bokeh + Pandas** (`/examples/bokeh/pandas`)
- CSV data loading and processing
- Interactive scatter plots with hover tooltips
- Pandas DataFrame operations

#### b) **Bokeh + NetworkX** (`/examples/bokeh/networks`)
- Graph visualization with Karate Club dataset
- Network analysis with NetworkX
- Interactive node/edge rendering

#### c) **Community Detection** (`/examples/bokeh/communities`)
- Graph clustering algorithms
- Visual community identification
- Color-coded node groupings

### 5. Diagrams as Code
**Path**: `/examples/diagrams`

Generate cloud architecture diagrams using Python's [diagrams](https://diagrams.mingrammer.com/) library:
- AWS/GCP/Azure architecture visualization
- Programmatic diagram creation
- Export to SVG format

### 6. Machine Learning - Digit Recognition
**Path**: `/examples/ml`

**Most Complex Example** - Interactive digit recognition with active learning:

**Features:**
- **Canvas Drawing**: Draw digits 0-9 with mouse/touch support
- **KNN Classification**: scikit-learn K-Nearest Neighbors (k=5, distance-weighted)
- **Active Learning**: Model learns from user feedback
  - ✓ **Positive Feedback**: Click YES to reinforce correct predictions
  - ✗ **Negative Feedback**: Click NO to correct and retrain
- **Real-time Visualization**: See what the model sees (8×8 preprocessed image)
- **Training Examples**: Browse the sklearn digits dataset
- **Adaptive Image Processing**:
  - LANCZOS resampling for quality
  - Adaptive thresholding for bounding box detection
  - Intensity scaling to match training distribution

**Key Implementation:**
- Image preprocessing: Canvas → Base64 → PIL → 8×8 grayscale → NumPy array
- Model persistence during session (no page refresh needed)
- Dynamic retraining with user corrections
- Training set grows from 1,437 to 1,437+N examples

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Clone the repository
git clone https://github.com/guinetik/pyscript-lab.git
cd pyscript-lab

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit `http://localhost:5173` to explore the examples.

### Building for Production

```bash
# Create optimized build
npm run build

# Preview production build
npm run preview
```

The build uses `@sveltejs/adapter-static` for static site generation, making it deployable to any static hosting service (GitHub Pages, Netlify, Vercel, etc.).

## Browser Compatibility

PyScript requires modern browsers with WebAssembly support:
- Chrome/Edge 90+
- Firefox 88+
- Safari 15+

## Key Learnings

1. **PyScript Initialization**: Load time depends on Python packages (first load ~5-10s)
2. **Memory Management**: Clean up Python script elements when components unmount
3. **Scope Isolation**: Use separate RunPython instances for scripts vs. inline code
4. **Console Access**: Use `console.log()` from Python to debug in browser DevTools
5. **Package Loading**: Configure packages in `<script type="py" config='{...}'>` tag

## Future Enhancements

- [ ] Add more ML examples (regression, clustering)
- [ ] Web Workers for heavy Python computations
- [ ] IndexedDB for model persistence
- [ ] Real-time collaborative features
- [ ] Performance benchmarks

## License

MIT

## Author

Created by [Guinetik](https://github.com/guinetik)

---

**Note**: This project uses PyScript 2025.2.1 which includes significant performance improvements over earlier versions. For production applications, consider the trade-offs between client-side Python execution and traditional server-side approaches.
