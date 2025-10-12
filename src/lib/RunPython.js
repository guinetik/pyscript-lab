/**
 * RunPython utility for dynamically executing Python code in PyScript
 * This utility creates and manages script elements for Python execution
 */

export default function RunPython() {
	let scriptElements = [];

	/**
	 * Run Python code from an external file
	 * @param {string} srcUrl - URL of the Python file to load
	 * @param {string} targetId - ID of the element where output should be displayed
	 * @param {boolean} showCode - Whether to display the code (default: true)
	 */
	function runScript(srcUrl, targetId, showCode = true) {
		const script = document.createElement('script');
		script.type = 'py';
		script.src = srcUrl;

		if (targetId) {
			script.setAttribute('target', targetId);
		}

		// Find target element or body
		const target = targetId ? document.getElementById(targetId) : document.body;
		if (target) {
			target.appendChild(script);
			scriptElements.push(script);
		}
	}

	/**
	 * Run inline Python code
	 * @param {string} code - Python code to execute
	 * @param {string} targetId - ID of the element where output should be displayed
	 * @param {boolean} showCode - Whether to display the code (default: true)
	 */
	function runCode(code, targetId, showCode = true) {
		const script = document.createElement('script');
		script.type = 'py';
		script.textContent = code;

		if (targetId) {
			script.setAttribute('target', targetId);
		}

		// Generate a unique ID for this script
		const scriptId = `py-script-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
		script.id = scriptId;

		// Find target element or body
		const target = targetId ? document.getElementById(targetId) : document.body;
		if (target) {
			target.appendChild(script);
			scriptElements.push(script);
		}
	}

	/**
	 * Clean up all script elements created by this runner
	 * @param {boolean} removeElements - Whether to remove the script elements from DOM (default: true)
	 */
	function destroy(removeElements = true) {
		if (removeElements) {
			scriptElements.forEach((script) => {
				if (script.parentNode) {
					script.parentNode.removeChild(script);
				}
			});
		}
		scriptElements = [];
	}

	return {
		runScript,
		runCode,
		destroy
	};
}
