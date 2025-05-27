<script>
	import { getLink } from './utils';
	import SiteMapStore from './SiteMapStore';
	import SiteMapLink from './SiteMapLink.svelte';
	import { page } from '$app/stores';
	import { beforeUpdate } from 'svelte';
	//
	let siteMap = null;
	let mobileLinks = [];
	let mainLinks = [];
	let visits = 0;
	let toggleBurgerMenu = false;
	//
	SiteMapStore.subscribe((s) => {
		siteMap = s;
		mainLinks = siteMap.getMainLinks();
		mobileLinks = siteMap.getMobileLinks();
	});
	beforeUpdate(() => {
		visits = window.visits;
	});
	export let activePage = '';
</script>

<nav class="bg-gray-100">
	<div class="mx-auto max-w-6xl px-4">
		<div class="flex justify-between">
			<div class="flex space-x-4">
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
							bind:active={$page.url.pathname}
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
					on:click={() => {
						toggleBurgerMenu = !toggleBurgerMenu;
					}}
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
						onclick={() => {
							toggleBurgerMenu = !toggleBurgerMenu;
						}}
						template={link.template}
						page={link.page}
						active={$page.url.pathname}
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
			on:click={() => {
				toggleBurgerMenu = !toggleBurgerMenu;
			}}
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
