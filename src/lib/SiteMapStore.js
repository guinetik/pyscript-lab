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
    new PageProp("next_page", getLink("/examples/bokeh/pandas")),
  ], [
    // Bokeh sub-pages
    new Page("bokeh_1", "Bokeh + Pandas", getLink("/examples/bokeh/pandas"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/bokeh")),
      new PageProp("next_page", getLink("/examples/bokeh/networks")),
    ]),
    new Page("bokeh_2", "Bokeh + NetworkX", getLink("/examples/bokeh/networks"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/bokeh/pandas")),
      new PageProp("next_page", getLink("/examples/bokeh/communities")),
    ]),
    new Page("bokeh_3", "Community Detection", getLink("/examples/bokeh/communities"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/bokeh/networks")),
      new PageProp("next_page", getLink("/examples/diagrams")),
    ]),
  ]),
  new Page("diagrams", "Diagrams as Code", getLink("/examples/diagrams"), [
    new PageProp("show", "all"),
    new PageProp("prev_page", getLink("/examples/bokeh/communities")),
    new PageProp("next_page", getLink("/examples/ml")),
  ]),
  new Page("ml", "Machine Learning", getLink("/examples/ml"), [
    new PageProp("show", "all"),
    new PageProp("prev_page", getLink("/examples/diagrams")),
    new PageProp("next_page", getLink("/examples/sentiment")),
  ], [
    // ML sub-pages
    new Page("ml_digit", "Digit Recognition", getLink("/examples/ml"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/diagrams")),
      new PageProp("next_page", getLink("/examples/sentiment")),
    ]),
    new Page("sentiment", "Sentiment Analysis", getLink("/examples/sentiment"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/ml")),
      new PageProp("next_page", getLink("/")),
    ]),
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
siteMap.setMainMenuTemplate("py-5 px-2 hover:text-yellow-500");
//////
siteMap.setMobileTemplate("block p-4 hover:text-white hover:bg-yellow-500");
//
export let SiteMapStore = writable(siteMap);
export default SiteMapStore;
