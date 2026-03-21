<script>
  /**
   * Layout container that wraps interactive PyScript examples with navigation controls.
   * @typedef {Object} ExperimentCardProps
   * @property {string} previousPage - URL to navigate to the previous example.
   * @property {string} nextPage - URL to navigate to the next example.
   * @property {'standard' | 'balanced'} [split='standard'] - Layout split ratio.
   */
  import { getLink } from "../utils.js";
  import { t } from 'svelte-i18n';

  /** @type {ExperimentCardProps} */
  export let props;
  
  // Default to standard if not provided
  const split = props.split || 'standard';
</script>
<main class="w-full min-h-[calc(100vh-120px)] flex flex-col">
  <div class="py-10 w-full flex-1 min-h-0 flex items-stretch justify-center">
    <div class="bg-surface rounded-lg shadow-card overflow-hidden w-10/12 flex flex-col min-h-0 border border-border">
      <!--     image -->
      <div class="md:flex flex-1 min-h-0">
        <section class="bg-surface-alt md:flex-grow md:w-full min-h-[380px] md:rounded-l-lg flex flex-col {split === 'balanced' ? 'lg:w-1/2' : 'lg:w-3/4'}">
          <slot name="py_slot" />
        </section>
        <section
          class="p-4 space-y-3 md:w-1/2 border-t border-border md:border-t-0 md:border-l md:rounded-r-lg flex flex-col bg-surface {split === 'balanced' ? 'lg:w-1/2' : 'lg:w-4/12'}"
        >
          <slot name="content_slot" />
          <div class="flex mt-auto pt-4 border-t border-border">
            <a
              href={getLink(props.previousPage)}
              class="text-xs py-2 px-3 border border-accent text-accent hover:bg-accent hover:text-white rounded transition-colors duration-200"
              ><img
                class="inline h-4"
                src={getLink("images/arrow-left.svg")}
                alt={$t('buttons.previous')}
              />{$t('buttons.previous')}
            </a>
            <a
              href={getLink(props.nextPage)}
              class="text-xs ml-auto py-2 px-3 border border-accent text-accent hover:bg-accent hover:text-white rounded transition-colors duration-200"
              >{$t('buttons.next')}<img
                class="inline h-4"
                src={getLink("images/arrow-next.svg")}
                alt={$t('buttons.next')}
              />
            </a>
          </div>
        </section>
      </div>
      <!--     footer -->
      <footer class="py-3 px-6 bg-dark text-xs text-white font-mono">
        <div id="script_gutter">

        </div>
      </footer>
    </div>
  </div>
</main>
