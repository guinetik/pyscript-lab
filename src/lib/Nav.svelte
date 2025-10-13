<script>
    /**
     * Responsive navigation bar that renders main and mobile menus derived from the site map.
     * @typedef {import('./SiteMap').SiteMap} SiteMap
     * @typedef {import('./SiteMap').Page} Page
     */
    import { getLink } from './utils';
    import SiteMapStore from './SiteMapStore';
    import SiteMapLink from './SiteMapLink.svelte';
    import { page } from '$app/stores';
    import { beforeUpdate } from 'svelte';

    /** @type {SiteMap | null} */
    let siteMap = null;
    /** @type {{ page: Page, template: string }[]} */
    let mobileLinks = [];
    /** @type {{ page: Page, template: string }[]} */
    let mainLinks = [];
    /** @type {number} */
    let visits = 0;
    /** @type {boolean} */
    let toggleBurgerMenu = false;

    SiteMapStore.subscribe((s) => {
        siteMap = s;
        mainLinks = siteMap.getMainLinks();
        mobileLinks = siteMap.getMobileLinks();
    });

    /**
     * Synchronizes the visit counter with the global tracker before each update cycle.
     * @returns {void}
     */
    function syncVisits() {
        visits = window.visits;
    }

    beforeUpdate(syncVisits);

    /**
     * Toggles the mobile navigation menu visibility.
     * @returns {void}
     */
    function toggleMenu() {
        toggleBurgerMenu = !toggleBurgerMenu;
    }

    /**
     * Closes the mobile navigation menu.
     * @returns {void}
     */
    function closeMenu() {
        toggleBurgerMenu = false;
    }

    /**
     * Currently active page pathname used to highlight navigation entries.
     * Allows parent components to override the highlighted link when provided.
     * @type {string}
     */
    export let activePage = '';

    /** @type {string} */
    $: currentPath = activePage || $page.url.pathname;
</script>

<nav class="bg-gray-100">
    <div class="mx-auto max-w-screen-2xl px-4">
        <div class="flex justify-between">
            <div class="flex space-x-2">
                <div>
                    <a
                        href={getLink('/')}
                        class="flex items-center px-2 py-5 text-gray-700 hover:text-gray-900"
                        ><img src={getLink('images/python.svg')} alt="PyScript L.A.B" />
                        <span class="font-bold">PyScript L.A.B</span></a
                    >
                </div>
                <div class="hidden items-center space-x-1 md:flex">
                    {#each mainLinks as link}
                        <SiteMapLink
                            template={link.template}
                            page={link.page}
                            active={currentPath}
                            activeClass="main_menu_active"
                        />
                    {/each}
                </div>
            </div>
            <div class="hidden items-center space-x-1 md:flex">
                <a href="https://github.com/guinetik/python-ds">
                    <img
                        src="https://img.shields.io/badge/-View Source-gray?style=flat-square&logo=github&logoColor=white&link=https://github.com/guinetik"
                        alt="Visits"
                    /></a
                >
                <a href="https://guinetik.github.io/python-ds/">
                    <img
                        src={`https://img.shields.io/static/v1?label=&message=${visits} Visitors&color=blueviolet&style=flat-square`}
                        alt="Visits"
                    /></a
                >
                <a href="https://linkedin.com/in/guinetik">
                    <img
                        src="https://img.shields.io/badge/-LinkedIn-blue?style=flat-square&logo=Linkedin&logoColor=white&link=https://www.linkedin.com/in/guinetik/"
                        alt="Linkedin"
                    /></a
                >
            </div>
            <div class="flex items-center justify-between md:hidden">
                <button
                    class="h-6 w-6"
                    on:click={toggleMenu}
                    aria-label="Toggle menu"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        class="h-6 w-6"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M4 6h16M4 12h16M4 18h16"
                        />
                    </svg>
                </button>
            </div>
        </div>
    </div>

    <!-- mobile menu -->
    <nav
        id="mobile-navigation"
        class="{toggleBurgerMenu
            ? 'visible opacity-100'
            : 'invisible opacity-0'} fixed top-0 right-0 bottom-0 left-0 z-10 backdrop-blur-sm transition-all duration-500"
    >
        <!-- UL Links -->
        <ul
            class="{toggleBurgerMenu
                ? 'translate-x-0'
                : 'translate-x-full'} absolute top-0 right-0 bottom-0 z-10 bg-white drop-shadow-2xl transition-all duration-500"
        >
            <div>
                <a
                    href={getLink('/')}
                    class="flex items-center px-2 py-5 text-gray-700 hover:text-gray-900"
                    ><img src={getLink('images/python.svg')} alt="PyScript L.A.B" />
                    <span class="font-bold">PyScript L.A.B</span></a
                >
            </div>
            {#each mobileLinks as link}
                <li class="border-b border-inherit">
                    <SiteMapLink
                        onclick={closeMenu}
                        template={link.template}
                        page={link.page}
                        active={currentPath}
                        activeClass="mobile_menu_active"
                    />
                </li>
            {/each}
        </ul>

        <!-- Close Button -->
        <button
            aria-label="Close menu"
            class="absolute top-0 right-0 bottom-0 left-0 {toggleBurgerMenu
                ? 'opacity-100'
                : 'opacity-0'}"
            on:click={closeMenu}
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                class="absolute top-2 left-2 h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                />
            </svg>
        </button>
    </nav>
</nav>
