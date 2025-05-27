import { dev } from "$app/environment";
import { goto } from "$app/navigation";
// something about svelte doesnt let me use links if i set a base
// https://github.com/sveltejs/kit/issues/4528
// so I created this little function that checks if it's dev, if not it appends the base path.
// I tried fetching the base path from the svelte.config.js but it complained in runtime since it needs nojs deps
// So this is the best I got so far, which is not bad, but I have to edit this path should I change the hosting for production
const basePath = "/python-ds";
/**
 * @param {string} page
 * @returns {string}
 */
export function getLink(page) {
	if (dev) return page.startsWith('/') ? page : '/' + page;
	else {
		return page !== '/' ? basePath + '/' + page : basePath;
	}
}
