<script>
  /**
   * Reusable documentation section for ExperimentCard right panels.
   * Provides consistent heading typography and optional ruled dividers.
   */
  let { title, divider = true, children } = $props();
</script>

{#if divider}
  <div class="border-t border-border pt-4 mt-4">
{:else}
  <div>
{/if}
  {#if title}
    <h3 class="font-heading text-lg font-bold text-text-primary mb-2">{title}</h3>
  {/if}
  <div class="text-sm text-text-primary font-body">
    {@render children()}
  </div>
</div>
