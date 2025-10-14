import { goto } from "$app/navigation";
import { base } from "$app/paths";

/**
 * @param {string} page
 * @returns {string}
 */
export function getLink(page) {
	// Ensure page starts with /
	const cleanPage = page.startsWith('/') ? page : '/' + page;
	// base is '' in dev, '/python-ds' in production (from svelte.config.js)
	return base + cleanPage;
}
