/**
 * Factory that produces helpers for dynamically executing PyScript snippets.
 * Maintains a registry of created `<script type="py">` elements for cleanup.
 *
 * @typedef {Object} RunPythonController
 * @property {(srcUrl: string, targetId?: string, showCode?: boolean) => void} runScript
 *   Loads and executes an external Python file.
 * @property {(code: string, targetId?: string, showCode?: boolean) => void} runCode
 *   Executes inline Python code.
 * @property {(removeElements?: boolean) => void} destroy
 *   Clears the registered script elements and optionally removes them from the DOM.
 *
 * @returns {RunPythonController}
 *
 * @author Guinetik
 */

export default function RunPython() {
    /** @type {HTMLScriptElement[]} */
    let scriptElements = [];

    /**
     * Run Python code from an external file.
     * @param {string} srcUrl - URL of the Python file to load.
     * @param {string} [targetId] - ID of the element where output should be displayed.
     * @param {boolean} [showCode=true] - Whether to display the code alongside execution.
     * @returns {void}
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
     * Run inline Python code.
     * @param {string} code - Python code to execute.
     * @param {string} [targetId] - ID of the element where output should be displayed.
     * @param {boolean} [showCode=true] - Whether to display the code alongside execution.
     * @returns {void}
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
     * Clean up all script elements created by this runner.
     * @param {boolean} [removeElements=true] - When true removes the script elements from the DOM.
     * @returns {void}
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
