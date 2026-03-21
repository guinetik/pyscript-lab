<script>
  /**
   * Green-tinted callout box for key concepts, tips, and warnings.
   * All types are visually identical for now but semantically typed.
   * @type {{ type?: 'info' | 'tip' | 'warning', children: import('svelte').Snippet }}
   */
  let { type = 'info', children } = $props();
</script>

<div class="rounded-sm bg-callout border-l-2 border-callout-border p-4 my-3">
  <div class="text-sm text-text-primary">
    {@render children()}
  </div>
</div>
