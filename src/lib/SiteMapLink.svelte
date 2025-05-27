<!-- 
    This component is a Svelte representation for a SiteMap page link
    The idea here is to onMount replace the component's contents with the SiteMap page link contents
 -->
<script>
  import { onMount } from "svelte";
  import SiteMapStore from "./SiteMapStore";
  import { SiteMap, Page } from "./SiteMap";
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

  $: activeSiteMapPage = siteMap.getPageByUrl(active);
  $: isActive = activeSiteMapPage && activeSiteMapPage.id === page.id;

  SiteMapStore.subscribe((s) => {
    siteMap = s;
  });
</script>
<a href={page.url} class={(isActive ? activeClass : '') + ' ' + template} on:click={onclick}>
  {page.title}
</a>