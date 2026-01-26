import { SiteMap, Page, PageProp } from "../SiteMap";
import { getLink } from "../utils.js";
import { writable } from "svelte/store";
//
const pages = [
  new Page("basics", "Basic Examples", getLink("/examples/basics/hello"), [
    new PageProp("show", "all"),
    new PageProp("prev_page", getLink("/")),
    new PageProp("next_page", getLink("/examples/basics/repl")),
  ], [
    // Basic Examples sub-pages
    new Page("hello-world", "Hello World", getLink("/examples/basics/hello"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/")),
      new PageProp("next_page", getLink("/examples/basics/repl")),
    ]),
    new Page("repl", "R.E.P.L", getLink("/examples/basics/repl"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/basics/hello")),
      new PageProp("next_page", getLink("/examples/basics/interop")),
    ]),
    new Page("interop", "Interoperability", getLink("/examples/basics/interop"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/basics/repl")),
      new PageProp("next_page", getLink("/examples/basics/encoder")),
    ]),
    new Page("encoder", "Advanced Interop", getLink("/examples/basics/encoder"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/basics/interop")),
      new PageProp("next_page", getLink("/examples/matplotlib/intro")),
    ]),
  ]),
  new Page("matplotlib", "Matplotlib", getLink("/examples/matplotlib/intro"), [
    new PageProp("show", "all"),
    new PageProp("prev_page", getLink("/examples/basics/encoder")),
    new PageProp("next_page", getLink("/examples/matplotlib/charts")),
  ], [
    // Matplotlib sub-pages
    new Page("matplotlib_intro", "Introduction", getLink("/examples/matplotlib/intro"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/basics/encoder")),
      new PageProp("next_page", getLink("/examples/matplotlib/charts")),
    ]),
    new Page("matplotlib_charts", "COVID-19 Charts", getLink("/examples/matplotlib/charts"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/matplotlib/intro")),
      new PageProp("next_page", getLink("/examples/matplotlib/maps")),
    ]),
    new Page("matplotlib_maps", "COVID-19 World Map", getLink("/examples/matplotlib/maps"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/matplotlib/charts")),
      new PageProp("next_page", getLink("/examples/bokeh")),
    ]),
  ]),
  new Page("bokeh_index", "Bokeh", getLink("/examples/bokeh"), [
    new PageProp("show", "all"),
    new PageProp("prev_page", getLink("/examples/matplotlib/maps")),
    new PageProp("next_page", getLink("/examples/bokeh/pandas")),
  ], [
    // Bokeh sub-pages
    new Page("bokeh_0", "Introduction", getLink("/examples/bokeh"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/matplotlib/maps")),
      new PageProp("next_page", getLink("/examples/bokeh/pandas")),
    ]),
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
      new PageProp("next_page", getLink("/examples/diagrams/gallery")),
    ]),
  ]),
  new Page("diagrams", "Diagrams as Code", getLink("/examples/diagrams/gallery"), [
    new PageProp("show", "all"),
    new PageProp("prev_page", getLink("/examples/bokeh/communities")),
    new PageProp("next_page", getLink("/examples/diagrams/create")),
  ], [
    // Diagrams sub-pages
    new Page("diagrams_gallery", "Diagrams Gallery", getLink("/examples/diagrams/gallery"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/bokeh/communities")),
      new PageProp("next_page", getLink("/examples/diagrams/create")),
    ]),
    new Page("diagrams_create", "Create Diagrams", getLink("/examples/diagrams/create"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/diagrams/gallery")),
      new PageProp("next_page", getLink("/examples/ml")),
    ]),
  ]),
  new Page("ml", "Machine Learning", getLink("/examples/ml"), [
    new PageProp("show", "all"),
    new PageProp("prev_page", getLink("/examples/diagrams/create")),
    new PageProp("next_page", getLink("/examples/sentiment")),
  ], [
    // ML sub-pages
    new Page("ml_digit", "Digit Recognition", getLink("/examples/ml"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/diagrams/create")),
      new PageProp("next_page", getLink("/examples/sentiment")),
    ]),
    new Page("sentiment", "Sentiment Analysis", getLink("/examples/sentiment"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/ml")),
      new PageProp("next_page", getLink("/examples/ml/rl")),
    ]),
    new Page("ml_rl", "Reinforcement Learning", getLink("/examples/ml/rl"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/sentiment")),
      new PageProp("next_page", getLink("/examples/ml/neuro")),
    ]),
    new Page("ml_neuro", "Neural Networks", getLink("/examples/ml/neuro"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/ml/rl")),
      new PageProp("next_page", getLink("/examples/ml/grokking")),
    ]),
    new Page("ml_grok", "Grokking", getLink("/examples/ml/grokking"), [
      new PageProp("show", "none"),
      new PageProp("prev_page", getLink("/examples/ml/neuro")),
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
