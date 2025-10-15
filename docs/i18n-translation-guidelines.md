# Translation Guidelines for PyScript Lab

Welcome! Thank you for helping translate PyScript Lab. This document provides guidelines to ensure consistent, high-quality translations.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Translation Principles](#translation-principles)
3. [Technical Guidelines](#technical-guidelines)
4. [Context and Glossary](#context-and-glossary)
5. [Quality Checklist](#quality-checklist)

## Getting Started

### What You Need
- Text editor (VS Code recommended with JSON extension)
- Basic understanding of JSON format
- Native or fluent proficiency in target language
- Familiarity with technical/programming terminology

### File Structure
Translation files are located in `src/lib/i18n/locales/`:
```
locales/
├── en.json    # English (base language)
├── es.json    # Spanish
├── pt.json    # Portuguese
├── zh.json    # Chinese
└── de.json    # German
```

### JSON Format Basics

```json
{
  "key": "Translation",
  "nested": {
    "key": "Nested translation"
  }
}
```

**Important**: 
- Always keep the keys (left side) unchanged
- Only translate the values (right side)
- Maintain proper JSON syntax (commas, quotes, brackets)

## Translation Principles

### 1. Accuracy First
Translate the **meaning**, not word-for-word. Ensure technical accuracy while maintaining natural language flow.

**Example**:
```json
// ✅ Good
"buttons.predict": "Predecir"  // Spanish - Natural and accurate

// ❌ Bad
"buttons.predict": "Prever"    // Technically correct but not commonly used
```

### 2. Consistency
Use the same translation for the same term throughout the application.

**Example**:
- If you translate "Machine Learning" as "Aprendizaje Automático", use it consistently
- Don't switch between "Aprendizaje Automático" and "Aprendizaje de Máquina"

### 3. Natural Language
Write how native speakers naturally speak. Avoid literal translations that sound awkward.

**Example**:
```json
// ✅ Good (German)
"home.subtitle": "Python im Browser. Kein Server erforderlich."

// ❌ Bad (overly literal)
"home.subtitle": "Python in dem Browser. Kein Server wird benötigt."
```

### 4. Cultural Adaptation
Adapt examples, idioms, and references to be culturally appropriate.

**Example**:
```json
// English uses "Hello World"
"examples.hello.title": "HELLO WORLD"

// Keep it in English or adapt culturally
// Spanish: Can keep "HELLO WORLD" or use "HOLA MUNDO"
"examples.hello.title": "HOLA MUNDO"
```

### 5. Respect Tone
PyScript Lab is educational and friendly. Maintain this tone in translations.

- Use friendly, approachable language
- Avoid overly formal or academic tone
- Keep it encouraging and accessible

## Technical Guidelines

### 1. Placeholders and Variables

**Never translate placeholder names** - they're replaced by code.

```json
// ✅ Correct
"nav.visitors": "{count} visitantes"

// ❌ Wrong
"nav.visitors": "{cantidad} visitantes"  // Don't change {count}!
```

**Common placeholders**:
- `{count}`, `{n}` - Numbers
- `{name}` - Names
- `{url}` - URLs
- `{#}` - Number in plurals

### 2. HTML Tags

Keep HTML tags unchanged.

```json
// ✅ Correct
"keyFeatures.stdLib": "Use módulos Python como <code>datetime</code>, <code>sys</code> y más"

// ❌ Wrong - removed HTML tags
"keyFeatures.stdLib": "Use módulos Python como datetime, sys y más"
```

### 3. Interpolation Syntax

Keep the interpolation syntax as-is:

```json
// ✅ Correct
"home.features.basic.count": "{n, plural, =0 {Sin ejemplos} one {# ejemplo} other {# ejemplos}}"

// ❌ Wrong - changed syntax
"home.features.basic.count": "{n: ningún ejemplo|un ejemplo|# ejemplos}"
```

### 4. Line Breaks

Maintain similar line length and structure:

```json
// English
"description": "Explore interactive examples demonstrating real-world Python applications."

// Spanish - similar length works well
"description": "Explora ejemplos interactivos que demuestran aplicaciones Python del mundo real."

// If much longer, consider breaking naturally
"description": "Explora ejemplos interactivos que demuestran aplicaciones de Python del mundo real."
```

### 5. Code and Technical Terms

**Do NOT translate**:
- Programming language names: Python, JavaScript, HTML
- Library/framework names: PyScript, Bokeh, Matplotlib, Svelte
- Code keywords: `print`, `import`, `class`
- File extensions: `.py`, `.js`, `.json`
- Command names: `npm install`, `git clone`

**DO translate**:
- UI labels: "Clear", "Predict", "Next"
- Descriptions of technical concepts
- Error messages
- Instructions

**Example**:
```json
// ✅ Correct (Spanish)
"examples.hello.description": "PyScript permite ejecutar código Python directamente en tu navegador web sin procesamiento del lado del servidor."

// ❌ Wrong - over-translated
"examples.hello.description": "PyScript permite ejecutar código Pitón directamente en tu navegador de web sin procesamiento del lado del servidor."
```

### 6. Punctuation

Follow target language punctuation rules:

**Spanish**: Use inverted question/exclamation marks
```json
"instruction": "¿Qué número dibujaste?"
"success": "¡Predicción correcta!"
```

**German**: Capitalize nouns
```json
"techStack.title": "Technologie-Stack"
```

**Chinese**: Use full-width punctuation
```json
"subtitle": "浏览器中的 Python，无需服务器。"
```

### 7. Text Length Considerations

Some languages are longer than English. Test your translations to ensure they fit in the UI.

**Typical expansion rates**:
- German: +30%
- Spanish: +20%
- French: +15%
- Portuguese: +15%
- Chinese: -30% (shorter!)

**Tips for long text**:
- Use abbreviations where culturally appropriate
- Restructure sentences for brevity
- Prioritize clarity over brevity

## Context and Glossary

### Application Context

**PyScript Lab** is an educational showcase demonstrating:
- Running Python in web browsers via WebAssembly
- Interactive coding examples
- Data visualization
- Machine learning in the browser
- No server required - everything runs client-side

**Target Audience**:
- Developers learning PyScript
- Python programmers interested in web technologies
- Students and educators
- Data scientists

### Key Terms Glossary

| English | Spanish | Portuguese | German | Chinese | Notes |
|---------|---------|------------|--------|---------|-------|
| Browser | Navegador | Navegador | Browser | 浏览器 | Keep "Browser" in German |
| Canvas | Lienzo | Tela | Leinwand | 画布 | HTML canvas element |
| Clear | Limpiar | Limpar | Löschen | 清除 | Button label |
| Console | Consola | Console | Konsole | 控制台 | Debug console |
| Dataset | Conjunto de datos | Conjunto de dados | Datensatz | 数据集 | |
| Digit Recognition | Reconocimiento de dígitos | Reconhecimento de dígitos | Ziffernerkennung | 数字识别 | |
| Example | Ejemplo | Exemplo | Beispiel | 示例 | |
| Feedback | Retroalimentación | Feedback | Rückmeldung | 反馈 | |
| Load | Cargar | Carregar | Laden | 加载 | |
| Machine Learning | Aprendizaje Automático | Aprendizado de Máquina | Maschinelles Lernen | 机器学习 | |
| Model | Modelo | Modelo | Modell | 模型 | ML model |
| Next | Siguiente | Próximo | Weiter | 下一个 | Navigation |
| Predict | Predecir | Prever | Vorhersagen | 预测 | ML prediction |
| Previous | Anterior | Anterior | Zurück | 上一个 | Navigation |
| Script | Script | Script | Skript | 脚本 | |
| Train | Entrenar | Treinar | Trainieren | 训练 | ML training |
| View Source | Ver código | Ver código | Quellcode anzeigen | 查看源码 | |
| Visualization | Visualización | Visualização | Visualisierung | 可视化 | |

### Section-Specific Context

#### Navigation
Concise menu labels. Should be short and clear.

#### Homepage
Marketing/promotional tone. Encourage exploration.

#### Example Pages
Educational tone. Clear instructions.

#### Error Messages
Helpful and actionable. Not scary.

#### Button Labels
Short (1-2 words ideally). Action-oriented.

## Quality Checklist

Before submitting your translation, verify:

### Technical Checks
- [ ] Valid JSON syntax (use a JSON validator)
- [ ] All keys from English file are present
- [ ] No extra keys added
- [ ] Placeholders unchanged (`{variable}`)
- [ ] HTML tags preserved
- [ ] No translation of code/technical terms

### Language Checks
- [ ] Spelling and grammar correct
- [ ] Consistent terminology throughout
- [ ] Natural-sounding phrases
- [ ] Appropriate tone (friendly, educational)
- [ ] Correct punctuation for target language
- [ ] Proper capitalization rules followed

### Context Checks
- [ ] Meaning preserved from English
- [ ] Culturally appropriate
- [ ] Technically accurate
- [ ] Length reasonable for UI
- [ ] Makes sense without seeing UI (but check UI if possible)

### Testing (if you can run the app)
- [ ] Text displays correctly (no encoding issues)
- [ ] UI doesn't break (text fits in buttons, etc.)
- [ ] All translated strings appear
- [ ] Navigation works
- [ ] No error messages about missing translations

## Common Mistakes to Avoid

### 1. Translating Code
```json
// ❌ Wrong
"codeExample": "imprimir('Hola Mundo')"  // Don't translate Python code

// ✅ Correct
"codeExample": "print('Hello World')"    // Keep code as-is
```

### 2. Changing JSON Structure
```json
// ❌ Wrong - changed structure
"buttons": "Limpiar, Predecir, Siguiente"

// ✅ Correct - maintained structure
"buttons": {
  "clear": "Limpiar",
  "predict": "Predecir",
  "next": "Siguiente"
}
```

### 3. Incomplete Translations
Don't leave English text in your translation file unless it's intentional (like brand names).

### 4. Over-translating
```json
// ❌ Wrong
"title": "PyScript Laboratorio.Aprendizaje.Base"

// ✅ Correct - keep brand name
"title": "PyScript L.A.B"
```

### 5. Forgetting Plurals
```json
// ❌ Wrong - only singular
"examples.count": "{n} ejemplo"

// ✅ Correct - plural forms
"examples.count": "{n, plural, =0 {Sin ejemplos} one {# ejemplo} other {# ejemplos}}"
```

## Examples of Good Translations

### Spanish (es.json)
```json
{
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
    "next": "Siguiente"
  }
}
```

### German (de.json)
```json
{
  "home": {
    "title": "PyScript L.A.B",
    "subtitle": "Python im Browser. Kein Server erforderlich.",
    "description": "Entdecken Sie interaktive Beispiele, die reale Python-Anwendungen demonstrieren, die vollständig in Ihrem Browser mit PyScript und modernen Webtechnologien laufen.",
    "startExploring": "Jetzt Erkunden",
    "learnMore": "Mehr Erfahren"
  },
  "buttons": {
    "clear": "Löschen",
    "predict": "Vorhersagen",
    "previous": "Zurück",
    "next": "Weiter"
  }
}
```

### Portuguese (pt.json)
```json
{
  "home": {
    "title": "PyScript L.A.B",
    "subtitle": "Python no Navegador. Sem Necessidade de Servidor.",
    "description": "Explore exemplos interativos demonstrando aplicações Python do mundo real executando completamente no seu navegador usando PyScript e tecnologias web modernas.",
    "startExploring": "Começar a Explorar",
    "learnMore": "Saiba Mais"
  },
  "buttons": {
    "clear": "Limpar",
    "predict": "Prever",
    "previous": "Anterior",
    "next": "Próximo"
  }
}
```

## Getting Help

### Questions About Context
If you're unsure about the context of a string:
1. Check the key name - it often indicates location
2. Look at surrounding keys in the JSON
3. Try to run the app and see where it appears
4. Ask the development team

### Technical Issues
If you encounter technical problems:
1. Validate JSON syntax: https://jsonlint.com/
2. Check character encoding (UTF-8)
3. Review the [migration guide](./i18n-migration-guide.md)

### Language Questions
When unsure about terminology:
1. Check glossary above
2. Search for similar translations in the same file
3. Consider what similar apps use
4. When in doubt, prioritize clarity

## Submission Process

1. **Complete translation** of assigned locale file
2. **Validate JSON** syntax
3. **Self-review** using quality checklist
4. **Test** if possible (run the app locally)
5. **Submit** via pull request or send to team
6. **Address feedback** from reviewers

## Recognition

All translators will be credited in:
- Project README.md
- About section of the application
- Release notes

Thank you for contributing to making PyScript Lab accessible to more people around the world!

---

**Need help?** Open an issue on GitHub or contact the maintainers.

**Found an error in existing translations?** Please report it or submit a fix!


