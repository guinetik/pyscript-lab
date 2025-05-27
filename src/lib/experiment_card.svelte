<script>
  import { getLink } from "./utils.js";
  export let props;
</script>
<main class="w-full h-[calc(100%-120px)]">
  <div class="py-10 w-full flex items-center justify-center h-full">
    <div class="bg-white rounded-lg shadow-2xl overflow-hidden w-10/12">
      <!--     image -->
      <div class="md:flex">
        <section class="bg-slate-300 lg:w-3/4 md:flex-grow md:w-full min-h-[380px] md:rounded-l-lg">
          <slot name="py_slot" />
        </section>
        <section
          class="p-4 space-y-3 md:w-1/2 lg:w-4/12 border-t border-slate-900 md:border-l md:rounded-r-lg"
        >
          <slot name="content_slot" />
          <div class="flex">
            <a
              href={getLink(props.previousPage)}
              class="text-xs ml-0 py-2 px-3 bg-blue-400 hover:bg-slate-300 text-slate-900 hover:text-slate-800 rounded transition duration-300"
              ><img
                class="inline h-4"
                src={getLink("images/arrow-left.svg")}
                alt="Next"
              />Previous
            </a>
            <a
              href={getLink(props.nextPage)}
              class="text-xs ml-auto py-2 px-3 bg-yellow-400 hover:bg-slate-300 text-slate-900 hover:text-slate-800 rounded transition duration-300"
              >Next<img
                class="inline h-4"
                src={getLink("images/arrow-next.svg")}
                alt="Next"
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
