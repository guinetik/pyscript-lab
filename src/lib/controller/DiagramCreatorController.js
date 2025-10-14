/**
 * DiagramCreatorController
 *
 * Orchestrates the interactive diagram creator functionality, separating business logic
 * from the Svelte UI layer. Handles:
 * - Initialization of viz.js (Graphviz WebAssembly)
 * - PyScript runner setup with diagram creator
 * - Template management
 * - Diagram generation and saving
 *
 * @author Guinetik
 */

import { DiagramRenderer } from '$lib/DiagramRenderer.js';
import RunPython from '$lib/RunPython.js';
import { getLink } from '$lib/utils.js';
import { createLogger } from '@guinetik/logger';

/**
 * @typedef {Object} Template
 * @property {string} name - Display name of the template
 * @property {string} code - Python code for the template
 */

export class DiagramCreatorController {
	/**
	 * Creates a new DiagramCreatorController instance.
	 */
	constructor() {
		/** @type {DiagramRenderer|null} */
		this.diagramRenderer = null;

		/** @type {RunPython|null} */
		this.pyScriptRunner = null;

		/** @type {boolean} */
		this.isInitialized = false;

		/** @type {Array<Template>} */
		this.templates = [
			{
				name: 'Simple Web Service',
				code: `from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

with Diagram("Simple Web Service", show=False):
    ELB("load balancer") >> EC2("web server") >> RDS("database")`
			},
			{
				name: 'Microservices',
				code: `from diagrams import Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.database import Dynamodb

with Diagram("Microservices API", show=False):
    api = APIGateway("api gateway")

    svc1 = Lambda("users service")
    svc2 = Lambda("orders service")

    db1 = Dynamodb("users db")
    db2 = Dynamodb("orders db")

    api >> [svc1, svc2]
    svc1 >> db1
    svc2 >> db2`
			},
			{
				name: 'Data Pipeline',
				code: `from diagrams import Diagram
from diagrams.aws.storage import S3
from diagrams.aws.compute import Lambda
from diagrams.aws.analytics import Athena

with Diagram("Data Pipeline", show=False):
    S3("raw data") >> Lambda("transform") >> S3("processed") >> Athena("analytics")`
			}
		];
	}

	/**
	 * Initialize the controller by setting up viz.js and PyScript.
	 *
	 * @returns {Promise<void>}
	 */
	async initialize() {
		this.logger = createLogger(
			{prefix: 'DiagramCreatorController',
			level: 'debug'});
		if (this.isInitialized) {
			console.warn('⚠️ DiagramCreatorController already initialized');
			return;
		}

		try {
			// Setup status callback
			this._setupStatusCallback();

			// Initialize viz.js for Graphviz rendering
			await this._initializeVizJs();

			// Initialize PyScript with diagram creator
			await this._initializePyScript();

			this.isInitialized = true;
			this.logger.log('✅ DiagramCreatorController initialized');
		} catch (error) {
			console.error('❌ Failed to initialize DiagramCreatorController:', error);
			throw error;
		}
	}

	/**
	 * Setup the status update callback for Python to call.
	 *
	 * @private
	 */
	_setupStatusCallback() {
		window.updateDiagramStatus = (newStatus, message) => {
			this.logger.log('🟢 updateDiagramStatus called:', newStatus, message);

			// Dispatch custom event for the UI to listen to
			window.dispatchEvent(
				new CustomEvent('diagramStatusUpdate', {
					detail: { status: newStatus, message: message }
				})
			);

			// Update output div on error
			if (newStatus === 'error') {
				const outputDiv = document.getElementById('user-diagram-output');
				if (outputDiv) {
					outputDiv.innerHTML = `<p class="text-red-600">❌ Error occurred</p>`;
				}
			}
		};

		this.logger.log('✅ Status callback setup complete');
	}

	/**
	 * Initialize viz.js (Graphviz compiled to WebAssembly).
	 *
	 * @private
	 * @returns {Promise<void>}
	 */
	async _initializeVizJs() {
		// Load viz.js dynamically
		const { instance } = await import('https://cdn.jsdelivr.net/npm/@viz-js/viz@3.2.0/+esm');
		const viz = await instance();
		this.logger.log('✅ Viz.js loaded');

		// Create DiagramRenderer instance
		this.diagramRenderer = new DiagramRenderer(viz);
		this.logger.log('✅ DiagramRenderer created');

		// Expose to window for Python to call
		window.diagramRenderer = this.diagramRenderer;
		window.fetchAndRenderDiagram = (chartId, dotContent, imageMappingJson) => {
			this.logger.log('🟢 fetchAndRenderDiagram called for:', chartId);
			this.diagramRenderer.render(chartId, dotContent, imageMappingJson);
		};
		window.renderDiagram = (chartId, dotContent) => {
			this.logger.log('🟢 renderDiagram called for:', chartId);
			this.diagramRenderer.renderSimple(chartId, dotContent);
		};

		this.logger.log('✅ DiagramRenderer exposed to window');
	}

	/**
	 * Initialize PyScript runner with diagram creator.
	 *
	 * @private
	 * @returns {Promise<void>}
	 */
	async _initializePyScript() {
		this.pyScriptRunner = RunPython();
		const pyScriptUrl = getLink('python/diagrams/diagram_creator.py');
		this.pyScriptRunner.runScript(pyScriptUrl, 'diagram-creator-script', false);

		// Wait for Python to be ready
		await this._waitForPythonReady();

		this.logger.log('✅ PyScript runner initialized');
	}

	/**
	 * Wait for Python's create_diagram function to be available.
	 *
	 * @private
	 * @returns {Promise<void>}
	 */
	_waitForPythonReady() {
		return new Promise((resolve, reject) => {
			let attempts = 0;
			const maxAttempts = 20; // 10 seconds max

			const checkReady = () => {
				attempts++;

				if (window.create_diagram) {
					this.logger.log('✅ Python create_diagram ready');
					resolve();
				} else if (attempts >= maxAttempts) {
					this.logger.error('❌ Timeout waiting for Python create_diagram');
					this.logger.error('Check browser console for Python errors');
					reject(new Error('Timeout waiting for Python to load. Check console for errors.'));
				} else {
					this.logger.log(`⏳ Waiting for Python create_diagram... (${attempts}/${maxAttempts})`);
					setTimeout(checkReady, 500);
				}
			};

			setTimeout(checkReady, 1000);
		});
	}

	/**
	 * Run the diagram generation with user code.
	 *
	 * @param {string} code - The Python code to execute
	 */
	runDiagram(code) {
		if (!this.isInitialized) {
			console.error('❌ Controller not initialized');
			return;
		}

		this.logger.log('🔵 runDiagram() called');

		// Clear previous output
		const outputDiv = document.getElementById('user-diagram-output');
		if (outputDiv) {
			outputDiv.innerHTML = '<p class="text-gray-500 animate-pulse">🔄 Generating diagram...</p>';
		}

		// Call Python function
		if (window.create_diagram) {
			this.logger.log('🔵 Calling window.create_diagram()');
			window.create_diagram(code);
		} else {
			console.error('🔴 window.create_diagram not found!');
			window.dispatchEvent(
				new CustomEvent('diagramStatusUpdate', {
					detail: {
						status: 'error',
						message: 'Python is not ready yet. Please wait a moment and try again.'
					}
				})
			);
		}
	}

	/**
	 * Save the current diagram as SVG.
	 *
	 * @returns {boolean} True if save was successful
	 */
	saveDiagram() {
		this.logger.log('🔵 saveDiagram() called');

		const outputDiv = document.getElementById('user-diagram-output');
		if (!outputDiv) {
			console.error('🔴 Output div not found');
			return false;
		}

		// Find the SVG element
		const svg = outputDiv.querySelector('svg');
		if (!svg) {
			console.error('🔴 No SVG found. Generate a diagram first.');
			alert('Please generate a diagram first before saving.');
			return false;
		}

		// Clone the SVG to avoid modifying the displayed one
		const svgClone = svg.cloneNode(true);

		// Get SVG as string
		const svgData = new XMLSerializer().serializeToString(svgClone);

		// Create blob
		const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });

		// Create download link
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = 'diagram.svg';

		// Trigger download
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);

		// Clean up
		URL.revokeObjectURL(url);

		this.logger.log('✅ Diagram saved!');
		return true;
	}

	/**
	 * Get all available templates.
	 *
	 * @returns {Array<Template>}
	 */
	getTemplates() {
		return this.templates;
	}

	/**
	 * Get a specific template by name.
	 *
	 * @param {string} name - Name of the template
	 * @returns {Template|undefined}
	 */
	getTemplate(name) {
		return this.templates.find((t) => t.name === name);
	}

	/**
	 * Clean up resources.
	 */
	destroy() {
		if (this.pyScriptRunner) {
			this.pyScriptRunner.destroy();
			this.pyScriptRunner = null;
		}

		// Clean up window references
		delete window.diagramRenderer;
		delete window.fetchAndRenderDiagram;
		delete window.renderDiagram;
		delete window.updateDiagramStatus;

		this.isInitialized = false;
		this.logger.log('✅ DiagramCreatorController destroyed');
	}
}

