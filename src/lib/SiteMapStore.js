import { SiteMap, Page, PageProp } from "./SiteMap";
import { getLink } from "./utils.js";
import { writable } from "svelte/store";
//
const pages = [
  new Page("hello-world", "Hello World", getLink("/examples/hello"), [
    new PageProp("show", "all"), // show in all menus
    new PageProp("prev_page", getLink("/")), // what page links to this
    new PageProp("next_page", getLink("/examples/repl")), // what page this links to
  ]),
  new Page("repl", "R.E.P.L", getLink("/examples/repl"), [
    new PageProp("show", "all"), // show in all menus
    new PageProp("prev_page", getLink("/examples/hello")), // what page links to this
    new PageProp("next_page", getLink("/examples/interop")), // what page this links to
  ]),
  new Page("interop", "Interoperability In Python", getLink("/examples/interop"), [
    new PageProp("show", "all"),
    new PageProp("prev_page", getLink("/examples/repl")),
    new PageProp("next_page", getLink("/examples/bokeh")),
  ]),
  new Page("bokeh_index", "Bokeh", getLink("/examples/bokeh"), [
    new PageProp("show", "all"),
    new PageProp("prev_page", getLink("/examples/interop")),
    new PageProp("next_page", getLink("/examples/bokeh-pandas")),
  ]),
  new Page("bokeh_1", "Bokeh + Pandas", getLink("/examples/bokeh-pandas"), [
    new PageProp("show", "none"), //show in no menus
    new PageProp("prev_page", getLink("/examples/bokeh")),
    new PageProp("next_page", getLink("/examples/bokeh-networkx")),
  ]),
  new Page("bokeh_2", "Bokeh + NetworkX", getLink("/examples/bokeh-networkx"), [
    new PageProp("show", "none"),
    new PageProp("prev_page", getLink("/examples/bokeh-pandas")),
    new PageProp("next_page", getLink("/examples/media")),
  ]),
  new Page("media", "Media", getLink("/examples/media"), [
    new PageProp("show", "all"),
    new PageProp("prev_page", getLink("/examples/bokeh-networkx")),
    new PageProp("next_page", getLink("/")),
  ]),
  new Page("github", "Github", "https://github.com/guinetik", [
    new PageProp("show", "mobile"), // shows only on mobile
  ]),
  new Page("twitter", "Twitter", "https://twitter.com/guinetik", [
    new PageProp("show", "mobile"), // shows only on mobile
  ]),
];
const siteMap = new SiteMap(pages);
//////
siteMap.setMainMenuTemplate("py-5 px-3 hover:text-yellow-500");
//////
siteMap.setMobileTemplate("block p-4 hover:text-white hover:bg-yellow-500");
//
export let SiteMapStore = writable(siteMap);
export default SiteMapStore;
