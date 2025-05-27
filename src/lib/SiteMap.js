/**
 * Experimenting with class-based javascript in 2022. Is there even a point to this?
 * Well OOP is a good strat when you want your code to follow a particular strucutre.
 * One aspect OOP helps a lot is avoidind code duplication.
 * This class manages a site menu and their templates in order to minimize code duplication
 */
export class SiteMap {
  /**
   * Creates a new SiteMap instance
   * @param {Array<Page>} pages - an array describing the pages of the site
   */
  constructor(pages) {
    this.sitePages = pages;
    const defaultTemplate = "<a href={url}>{title}</a>";
    this.templates = {
      main: defaultTemplate,
      mobile: defaultTemplate,
    };
  }
  /**
   * Sets the template for creating links for the main menu
   * @param {String} t - the template string.
   */
  setMainMenuTemplate(t) {
    this.templates.main = t;
  }
  /**
   * Sets the template for creating links for the mobile menu
   * @param {String} t  - the template string
   */
  setMobileTemplate(t) {
    this.templates.mobile = t;
  }
  /**
   * Sets the template for creating any additional custom menu
   * @param {String} name - name of the custom template
   * @param {String} t - the template string
   */
  setCustomTemplate(name, t) {
    if (typeof name === 'string' && typeof t === 'string') {
      this.templates[name] = t;
    }
  }

  /**
   * Helper function to find a page from its id
   * @param {String} id - the page Id to search for
   * @returns {Page} the page with that ID or undefined
   */
  getPageById(id) {
    return this.sitePages.find((p) => id === p.id) || null;
  }

  /**
   * Helper function to find a page from its url
   * @param {String} url - the page Id to search for
   * @returns {Page} the page with that url or undefined
   */
   getPageByUrl(url) {
    return this.sitePages.find((p) => url === p.url) || null;
  }

  /**
   *
   * @param {String} pageId - Id of the page
   * @param {String} t - the Template to generate the link
   * @returns {Object} - an object containing the template link and a reference to a Page object
   */
  getPageLink(pageId, t) {
    const page = this.getPageById(pageId);
    if (!page) return null;
    page.setProp("title", page.title);
    page.setProp("url", page.url);
    const props = page.props.reduce((accumulator, currentValue) => {
      accumulator.value = accumulator.value + "," + currentValue.name;
      return accumulator;
    }, new PageProp("props", "title,url"));
    let tp = this.templates[t];
    if (typeof tp !== 'string') return null;
    props.value.split(",").forEach((p) => {
      tp = tp.replaceAll("{" + p + "}", page.getProp(p)?.value || '');
    });
    return {
      page: page,
      template: tp
    };
  }

  /**
   * Get links for a mobile menu.
   * @returns {Array<String>} an array of strings where each item is a templated link to a page in the mobile menu
   */
  getMobileLinks() {
    const m = "mobile";
    return this.getLinks(m, m);
  }
  /**
   * Get links for a mobile menu.
   * @returns {Array<String>} an array of strings where each item is a templated link to a page in the mobile menu
   */
   getMainLinks() {
    const m = "main";
    return this.getLinks(m, m);
  }
  /**
   * Get links for a specific menu.
   * @param {string} template - The template to use for the links.
   * @param {string} show - The visibility setting for the links.
   * @returns {Array<{ page: Page, template: string }>} An array of link objects.
   */
  getLinks(template, show) {
    const links = [];
    this.sitePages.forEach((page) => {
      const showProp = page.getProp("show")?.value || "no";
      if (showProp === show || showProp === "all") {
        const link = this.getPageLink(page.id, template);
        if (link) links.push(link);
      }
    });
    return links;
  }
}
/**
 * PageProp hold custom property
 */
export class PageProp {
  /**
   * A map item for page props
   * @param {String} name prop name
   * @param {Object} value propValue
   */
  constructor(name, value) {
    this.name = name;
    this.value = value;
  }
}
/**
 * Defines a page on our site
 */
export class Page {
  /**
   * Creates a new Page
   * @param {String} id the ID for the page
   * @param {String} title - Page title
   * @param {String} url - Page Url
   * @param {Array<PageProp>} props - An array of PageProp objects
   */
  constructor(id, title, url, props) {
    this.id = id;
    this.title = title;
    this.url = url;
    this.props = props;
  }
  /**
   * Gets a page property by name
   * @param {String} name - Name of the prop
   * @returns {PageProp} the property of the pages
   */
  getProp(name) {
    return this.props.find((p) => name === p.name);
  }
  setProp(name, value) {
    this.props.push(new PageProp(name, value));
  }
}
export default SiteMap;
