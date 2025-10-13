<script>
    /**
     * Wrapper component that renders a PyScript example alongside the highlighted source code.
     * @typedef {Object} PyExampleProps
     * @property {string} [title] - Optional title displayed above the highlighted source.
     */
    import CodeBlock from './CodeBlock.svelte';
    import { onMount } from 'svelte';

    /** @type {PyExampleProps['title']} */
    let { title = '' } = $props();
    /** @type {string} */
    let sourceCode = $state('');
    /** @type {string} */
    let scriptId = $state('');
    /** @type {HTMLElement | null | undefined} */
    let scriptElement;

    /**
     * Loads the PyScript source from the rendered slot and updates highlighted output.
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
    <CodeBlock code={sourceCode} />
    <div id={scriptId} class="output mt-4" bind:this={scriptElement}>
        <slot />
    </div>
</div> 