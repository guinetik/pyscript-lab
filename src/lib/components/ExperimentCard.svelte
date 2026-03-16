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
    <div class="bg-white rounded-lg shadow-2xl overflow-hidden w-10/12 flex flex-col min-h-0">
      <!--     image -->
      <div class="md:flex flex-1 min-h-0">
        <section class="bg-slate-300 md:flex-grow md:w-full min-h-[380px] md:rounded-l-lg flex flex-col {split === 'balanced' ? 'lg:w-1/2' : 'lg:w-3/4'}">
          <slot name="py_slot" />
        </section>
        <section
          class="p-4 space-y-3 md:w-1/2 border-t border-slate-900 md:border-l md:rounded-r-lg flex flex-col {split === 'balanced' ? 'lg:w-1/2' : 'lg:w-4/12'}"
        >
          <slot name="content_slot" />
          <div class="flex">
            <a
              href={getLink(props.previousPage)}
              class="text-xs ml-0 py-2 px-3 bg-blue-400 hover:bg-slate-300 text-slate-900 hover:text-slate-800 rounded transition duration-300"
              ><img
                class="inline h-4"
                src={getLink("images/arrow-left.svg")}
                alt={$t('buttons.previous')}
              />{$t('buttons.previous')}
            </a>
            <a
              href={getLink(props.nextPage)}
              class="text-xs ml-auto py-2 px-3 bg-yellow-400 hover:bg-slate-300 text-slate-900 hover:text-slate-800 rounded transition duration-300"
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
      <footer class="py-3 px-6 bg-slate-800 text-xs text-white font-mono">
        <div id="script_gutter">

        </div>
      </footer>
    </div>
  </div>
</main>
