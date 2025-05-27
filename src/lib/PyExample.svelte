<script>
    import CodeBlock from './CodeBlock.svelte';
    import { onMount } from 'svelte';
    
    let { title = '' } = $props();
    let sourceCode = $state('');
    let scriptId = $state('');
    let scriptElement;

    onMount(async () => {
        // Get the script element from the slot
        const script = scriptElement?.querySelector('script[type="py"]');
        if (script) {
            // Preserve the original script ID
            scriptId = script.id || '';
            
            if (script.src) {
                // If we have a src attribute, fetch the content
                try {
                    const response = await fetch(script.src);
                    sourceCode = await response.text();
                } catch (e) {
                    console.error('Failed to fetch source code:', e);
                }
            } else {
                // If it's inline script, use its content
                sourceCode = script.textContent || '';
            }
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