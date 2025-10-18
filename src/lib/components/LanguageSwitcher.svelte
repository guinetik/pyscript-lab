<script>
	/**
	 * Language switcher dropdown component.
	 * Allows users to change the application locale and persists the selection.
	 */
	import { locale } from 'svelte-i18n';
	import { AVAILABLE_LOCALES, changeLocale } from '$lib/i18n';

	let isOpen = $state(false);

	/**
	 * Toggle dropdown visibility
	 * @returns {void}
	 */
	function toggleDropdown() {
		isOpen = !isOpen;
	}

	/**
	 * Close dropdown
	 * @returns {void}
	 */
	function closeDropdown() {
		isOpen = false;
	}

	/**
	 * Handle locale selection
	 * @param {string} newLocale - The locale code to switch to
	 * @returns {void}
	 */
	function selectLocale(newLocale) {
		changeLocale(newLocale);
		closeDropdown();
	}

	let currentLocale = $derived($locale || 'en');
	let currentLanguage = $derived(AVAILABLE_LOCALES[currentLocale]);
</script>

<div class="relative">
	<button
		onclick={toggleDropdown}
		class="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-gray-100 transition-colors"
		aria-label="Select language"
		aria-expanded={isOpen}
		aria-haspopup="true"
	>
		<span class="text-xl">{currentLanguage?.flag}</span>
		<span class="font-medium text-gray-700">{currentLanguage?.name}</span>
		<svg
			class="h-4 w-4 transition-transform {isOpen ? 'rotate-180' : ''}"
			fill="none"
			stroke="currentColor"
			viewBox="0 0 24 24"
		>
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
		</svg>
	</button>

	{#if isOpen}
		<div
			class="absolute right-0 mt-2 w-48 rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5 z-50"
			role="menu"
		>
			<div class="py-1">
				{#each Object.values(AVAILABLE_LOCALES) as language}
					<button
						onclick={() => selectLocale(language.code)}
						class="block w-full text-left px-4 py-2 text-sm hover:bg-gray-100 {currentLocale === language.code ? 'bg-yellow-50 text-yellow-600 font-bold' : 'text-gray-700'}"
						role="menuitem"
					>
						<span class="mr-2">{language.flag}</span>
						{language.name}
					</button>
				{/each}
			</div>
		</div>
	{/if}
</div>

<!-- Close dropdown when clicking outside -->
{#if isOpen}
	<button
		class="fixed inset-0 z-40"
		onclick={closeDropdown}
		aria-label="Close dropdown"
		tabindex="-1"
	></button>
{/if}
