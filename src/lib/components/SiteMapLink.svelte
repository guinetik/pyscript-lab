<!-- 
    This component is a Svelte representation for a SiteMap page link
    The idea here is to onMount replace the component's contents with the SiteMap page link contents
 -->
<script>
  /**
   * Hyperlink component bound to a `SiteMap` entry that highlights when active.
   * Internally resolves the current page from the shared `SiteMapStore` to compute active state.
   * @typedef {import('../SiteMap').SiteMap} SiteMap
   * @typedef {import('../SiteMap').Page} Page
   */
  import { onMount } from "svelte";
  import SiteMapStore from "../stores/SiteMapStore";
  import { SiteMap, Page } from "../SiteMap";
  //
  /**
   * @type {String}
   **/
  export let template;
  /**
   * @type {String}
   **/
  export let active;
  /**
   * @type {String}
   **/
  export let activeClass = "active";
  /**
   * @type {Page}
   *
   **/
  export let page;
  /**
   * @type {Function}
   */
  export let onclick;
  /**
   * @type {SiteMap}
   */
  let siteMap;
  /**
   * @type {Page}
   */
  let activeSiteMapPage;
  /**
   * @type {Boolean}
   */
  let isActive;

  // Reactive statement: Update activeSiteMapPage whenever siteMap or active changes
  $: activeSiteMapPage = siteMap.getPageByUrl(active);

  // Reactive statement: Update isActive by comparing URLs directly
  $: isActive = active === page.url;

  // Subscribe to SiteMapStore updates and update siteMap accordingly
  SiteMapStore.subscribe((s) => {
    siteMap = s;
  });
</script>
<a href={page.url} class={(isActive ? activeClass : '') + ' ' + template} on:click={onclick}>
  {page.title}
</a>