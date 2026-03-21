<script>
    /**
     * Wrapper component that renders a PyScript example alongside the highlighted source code.
     * @typedef {Object} PyExampleProps
     * @property {string} [title] - Optional title displayed above the highlighted source.
     * @property {import('svelte').Snippet} [children] - Snippet containing the PyScript code to render.
     */
    import CodeBlock from './CodeBlock.svelte';
    import { onMount } from 'svelte';

    /** @type {PyExampleProps['title']} */
    let { title = '', children } = $props();
    /** @type {string} */
    let sourceCode = $state('');
    /** @type {string} */
    let scriptId = $state('');
    /** @type {HTMLElement | null | undefined} */
    let scriptElement;
    /** @type {boolean} */
    let isCodeVisible = $state(false);

    /**
     * Loads the PyScript source from the rendered snippet and updates highlighted output.
     * @param {HTMLScriptElement} script - Script element containing or referencing Python code.
     * @returns {Promise<void>}
     */
    async function hydrateSourceFromScript(script) {
        scriptId = script.id || '';

        if (script.src) {
            try {
                const response = await fetch(script.src);
                sourceCode = await response.text();
            } catch (e) {
                console.error('Failed to fetch source code:', e);
                sourceCode = '';
            }
        } else {
            sourceCode = script.textContent || '';
        }
    }

    /**
     * Toggles the visibility of the code block.
     */
    function toggleCode() {
        isCodeVisible = !isCodeVisible;
    }

    onMount(async () => {
        const script = scriptElement?.querySelector('script[type="py"]');
        if (script) {
            await hydrateSourceFromScript(script);
        }
    });
</script>

<div class="py-example">
    {#if title}
        <p class="mb-2">{title}</p>
    {/if}

    <!-- Toggle button -->
    <button
        onclick={toggleCode}
        class="mb-3 flex items-center gap-2 text-sm text-accent hover:text-accent/80 font-medium transition-colors"
        aria-expanded={isCodeVisible}
    >
        <svg
            class="w-4 h-4 transition-transform duration-200 {isCodeVisible ? 'rotate-90' : ''}"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
        >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
        </svg>
        {isCodeVisible ? 'Hide code' : 'See the code'}
    </button>

    <!-- Collapsible code block -->
    {#if isCodeVisible}
        <div class="code-container transition-all duration-300 ease-in-out">
            <CodeBlock code={sourceCode} />
        </div>
    {/if}

    <div id={scriptId} class="output mt-4" bind:this={scriptElement}>
        {#if children}
            {@render children()}
        {/if}
    </div>
</div> 