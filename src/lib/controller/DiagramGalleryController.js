/**
 * DiagramGalleryController
 *
 * Orchestrates the diagram gallery functionality, separating business logic
 * from the Svelte UI layer. Handles:
 * - Initialization of viz.js (Graphviz WebAssembly)
 * - PyScript runner setup with diagram manager
 * - Registration of diagram examples
 * - Coordination between Python and JavaScript
 *
 * @author Guinetik
 */

import { DiagramRenderer } from '$lib/DiagramRenderer.js';
import RunPython from '$lib/RunPython.js';
import { getLink } from '$lib/utils.js';
import { createLogger } from '@guinetik/logger';

/**
 * @typedef {Object} DiagramExample
 * @property {string} id - Unique identifier for the example
 * @property {string} name - Display name of the example
 * @property {string} file - Path to the Python file
 */

export class DiagramGalleryController {
	/**
	 * Creates a new DiagramGalleryController instance.
	 */
	constructor() {
		/** @type {DiagramRenderer|null} */
		this.diagramRenderer = null;

		/** @type {RunPython|null} */
		this.pyScriptRunner = null;

		/** @type {boolean} */
		this.isInitialized = false;

		/** @type {Array<DiagramExample>} */
		this.examples = [];
	}

	/**
	 * Initialize the controller by setting up viz.js and PyScript.
	 *
	 * @returns {Promise<void>}
	 */
	async initialize() {
		this.logger = createLogger(
			{prefix: 'DiagramGalleryController',
			level: 'debug'});
		if (this.isInitialized) {
			this.logger.warn('⚠️ DiagramGalleryController already initialized');
			return;
		}

		try {
			// Initialize viz.js for Graphviz rendering
			await this._initializeVizJs();

			// Initialize PyScript with diagram manager
			await this._initializePyScript();

			// Register all diagram examples
			this._registerExamples();

			// Generate all diagrams
			this._generateAllDiagrams();

			this.isInitialized = true;
			this.logger.log('✅ DiagramGalleryController initialized');
		} catch (error) {
			this.logger.error('❌ Failed to initialize DiagramGalleryController:', error);
			throw error;
		}
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
		this.logger.log('✅ Viz.js loaded and ready!');

		// Create DiagramRenderer instance
		this.diagramRenderer = new DiagramRenderer(viz);
		this.logger.log('✅ DiagramRenderer created!');

		// Expose to window for Python to call
		window.diagramRenderer = this.diagramRenderer;
		window.fetchAndRenderDiagram = (chartId, dotContent, imageMappingJson) => {
			this.diagramRenderer.render(chartId, dotContent, imageMappingJson);
		};
		window.renderDiagram = (chartId, dotContent) => {
			this.diagramRenderer.renderSimple(chartId, dotContent);
		};

		this.logger.log('✅ DiagramRenderer exposed to window');
	}

	/**
	 * Initialize PyScript runner with diagram manager.
	 *
	 * @private
	 * @returns {Promise<void>}
	 */
	async _initializePyScript() {
		return new Promise((resolve) => {
			this.pyScriptRunner = RunPython();
			this.pyScriptRunner.runScript(
				getLink('python/diagrams/diagram_manager.py'),
				'script_gutter',
				false
			);

			// Wait for Python manager to be ready
			const checkManager = () => {
				if (window.manager) {
					this.logger.log('✅ PyScript runner initialized, manager ready');
					resolve();
				} else {
					this.logger.log('⏳ Waiting for Python manager...');
					setTimeout(checkManager, 500);
				}
			};
			
			setTimeout(checkManager, 1000);
		});
	}

	/**
	 * Register all diagram examples with the Python manager.
	 *
	 * @private
	 */
	_registerExamples() {
		this.examples = [
			{
				id: 'chart1',
				name: 'Grouped Workers',
				file: 'python/diagrams/grouped_workers.py'
			},
			{
				id: 'chart2',
				name: 'Clustered Web Services',
				file: 'python/diagrams/clustered_services.py'
			},
			{
				id: 'chart3',
				name: 'Event-Driven Architecture',
				file: 'python/diagrams/event_driven.py'
			},
			{
				id: 'chart4',
				name: 'Microservices API',
				file: 'python/diagrams/microservices_api.py'
			},
			{
				id: 'chart5',
				name: 'Data Analytics Pipeline',
				file: 'python/diagrams/data_pipeline.py'
			}
		];

		// Register each example with the Python manager
		this.examples.forEach((example) => {
			const fullPath = getLink(example.file);
			window.manager.addExample(example.name, example.id, fullPath);
		});

		this.logger.log(`✅ Registered ${this.examples.length} diagram examples`);
	}

	/**
	 * Generate all diagrams initially.
	 *
	 * @private
	 */
	_generateAllDiagrams() {
		// Give a moment for everything to settle, then generate all diagrams
		setTimeout(() => {
			this.logger.log('🚀 Generating all diagrams...');
			window.manager.generateAll();
		}, 1000);
	}

	/**
	 * Regenerate a specific diagram.
	 *
	 * @param {string} exampleId - The ID of the example to regenerate
	 */
	regenerateDiagram(exampleId) {
		if (!this.isInitialized) {
			this.logger.error('❌ Controller not initialized');
			return;
		}

		this.logger.log(`🔄 Regenerating diagram: ${exampleId}`);
		window.generateExample(exampleId);
	}

	/**
	 * Get example by ID.
	 *
	 * @param {string} exampleId - The ID of the example
	 * @returns {DiagramExample|undefined}
	 */
	getExample(exampleId) {
		return this.examples.find((ex) => ex.id === exampleId);
	}

	/**
	 * Get all registered examples.
	 *
	 * @returns {Array<DiagramExample>}
	 */
	getAllExamples() {
		return this.examples;
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

		this.isInitialized = false;
		this.logger.log('✅ DiagramGalleryController destroyed');
	}
}

