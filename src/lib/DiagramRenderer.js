/**
 * DiagramRenderer - Client-side diagram rendering with viz.js and icon injection
 *
 * This class handles the browser-side rendering of Graphviz DOT diagrams generated
 * by the Python Diagrams library. It coordinates between:
 * 1. viz.js (Graphviz compiled to WebAssembly) for SVG generation
 * 2. GitHub icon fetching and caching
 * 3. Manual SVG icon injection (since viz.js doesn't support image attributes)
 *
 * @author Guinetik
 */

export class DiagramRenderer {
	/**
	 * Initialize the diagram renderer
	 *
	 * @param {Object} vizInstance - The viz.js instance for rendering DOT to SVG
	 */
	constructor(vizInstance) {
		this.viz = vizInstance;
		this.imageCache = {};
		//console.log('🎨 DiagramRenderer initialized');
	}

	/**
	 * Fetch a URL with retry logic and exponential backoff
	 *
	 * @param {string} url - URL to fetch
	 * @param {number} maxRetries - Maximum number of retry attempts
	 * @param {number} baseDelay - Base delay in milliseconds for exponential backoff
	 * @returns {Promise<Blob>} The fetched blob
	 * @throws {Error} If all retry attempts fail
	 */
	async fetchWithRetry(url, maxRetries = 3, baseDelay = 1000) {
		for (let i = 0; i < maxRetries; i++) {
			try {
				const response = await fetch(url);
				if (!response.ok) {
					throw new Error(`HTTP ${response.status}: ${response.statusText}`);
				}
				return await response.blob();
			} catch (err) {
				const isLastAttempt = i === maxRetries - 1;
				console.warn(`⚠️ Attempt ${i + 1}/${maxRetries} failed for ${url}:`, err.message);

				if (isLastAttempt) throw err;

				// Exponential backoff: 1s, 2s, 4s
				const delay = baseDelay * Math.pow(2, i);
				//console.log(`⏳ Waiting ${delay}ms before retry...`);
				await new Promise(resolve => setTimeout(resolve, delay));
			}
		}
	}

	/**
	 * Convert a blob to a data URI
	 *
	 * @param {Blob} blob - The blob to convert
	 * @returns {Promise<string>} Base64 data URI
	 */
	async blobToDataUri(blob) {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onloadend = () => resolve(reader.result);
			reader.onerror = reject;
			reader.readAsDataURL(blob);
		});
	}

	/**
	 * Fetch and cache all images for a diagram
	 *
	 * @param {Object} imageMapping - Map of local paths to GitHub URLs
	 * @returns {Promise<Object>} Object containing dataUriCache and fetch results
	 */
	async fetchImages(imageMapping) {
		const dataUriCache = {};

		const fetchPromises = Object.entries(imageMapping).map(async ([localPath, githubUrl]) => {
			try {
				// Check global cache first
				if (this.imageCache[githubUrl]) {
					//console.log('💾 Using cached image:', githubUrl);
					dataUriCache[localPath] = this.imageCache[githubUrl];
					return { success: true, localPath, cached: true };
				}

				//console.log('📥 Fetching:', githubUrl);
				const blob = await this.fetchWithRetry(githubUrl);
				const dataUri = await this.blobToDataUri(blob);

				dataUriCache[localPath] = dataUri;
				this.imageCache[githubUrl] = dataUri; // Store in global cache
				//console.log('✅ Fetched and cached:', localPath);
				return { success: true, localPath, cached: false };
			} catch (err) {
				console.error('❌ Failed to fetch after retries:', githubUrl, err);
				return { success: false, localPath, error: err.message };
			}
		});

		const results = await Promise.all(fetchPromises);
		const failed = results.filter(r => !r.success);
		const cached = results.filter(r => r.success && r.cached).length;
		const fetched = results.filter(r => r.success && !r.cached).length;

		if (failed.length > 0) {
			console.warn(`⚠️ Failed to fetch ${failed.length} images:`, failed.map(f => f.localPath));
		}
		//console.log(`🎉 Images ready: ${Object.keys(dataUriCache).length} total (${fetched} fetched, ${cached} from cache)`);

		return { dataUriCache, failed, cached, fetched };
	}

	/**
	 * Parse DOT source to create node ID and label mappings to images
	 *
	 * @param {string} dotContent - The Graphviz DOT source code
	 * @param {Object} dataUriCache - Map of local paths to data URIs
	 * @returns {Object} Object with nodeImageMap and labelImageMap
	 */
	createImageMappings(dotContent, dataUriCache) {
		const nodeImageMap = {}; // node ID -> dataUri
		const labelImageMap = {}; // label text -> dataUri

		//console.log('🔍 Parsing DOT for node-to-image mapping...');
		const lines = dotContent.split('\n');

		for (const line of lines) {
			// Skip lines without image attribute
			if (!line.includes('image=')) continue;

			//console.log('📝 Processing line:', line.trim());

			// Find which image path is in this line
			for (const [localPath, dataUri] of Object.entries(dataUriCache)) {
				if (line.includes(localPath)) {
					// Extract node ID - try multiple patterns
					// Pattern 1: "nodeId" [label=...
					let nodeMatch = line.match(/"([^"]+)"\s*\[/);

					// Pattern 2: nodeId [label=... (without quotes)
					if (!nodeMatch) {
						nodeMatch = line.match(/^\s*([^\s\[]+)\s*\[/);
					}

					// Also extract label text as fallback
					const labelMatch = line.match(/label="([^"]+)"/);

					if (nodeMatch) {
						const nodeId = nodeMatch[1];
						if (!nodeImageMap[nodeId]) {
							nodeImageMap[nodeId] = dataUri;
							//console.log('🗺️ Mapped node ID', nodeId, '→ image');
						}
					}

					if (labelMatch) {
						const labelText = labelMatch[1];
						if (!labelImageMap[labelText]) {
							labelImageMap[labelText] = dataUri;
							//console.log('🗺️ Mapped label', labelText, '→ image');
						}
					}

					if (!nodeMatch && !labelMatch) {
						console.warn('⚠️ Could not extract node ID or label from line:', line.trim());
					}
					break; // Found the image for this line, move to next line
				}
			}
		}

		//console.log('🗺️ Node ID map:', nodeImageMap);
		//console.log('🗺️ Label map:', labelImageMap);
		//console.log('🗺️ Total nodes mapped:', Object.keys(nodeImageMap).length);
		//console.log('🗺️ Total labels mapped:', Object.keys(labelImageMap).length);

		if (Object.keys(nodeImageMap).length === 0 && Object.keys(labelImageMap).length === 0) {
			console.error('❌ NO MAPPINGS CREATED! Check DOT format');
		}

		return { nodeImageMap, labelImageMap };
	}

	/**
	 * Inject images into SVG nodes manually
	 *
	 * viz.js doesn't support image attributes, so we manually inject SVG image elements
	 * into the rendered SVG based on node positions.
	 *
	 * @param {SVGElement} svg - The rendered SVG element
	 * @param {Object} nodeImageMap - Map of node IDs to data URIs
	 * @param {Object} labelImageMap - Map of label text to data URIs (fallback)
	 * @returns {number} Number of images successfully injected
	 */
	injectImages(svg, nodeImageMap, labelImageMap) {
		const nodes = svg.querySelectorAll('g.node');
		//console.log(`🎨 Found ${nodes.length} nodes to process`);

		// First, log all SVG node IDs for debugging
		//console.log('🔍 SVG nodes found:');
		nodes.forEach((node, idx) => {
			const title = node.querySelector('title');
			if (title) {
				//console.log(`  [${idx}] Title: "${title.textContent.trim()}"`);
			}
		});

		let injectedCount = 0;

		nodes.forEach((node) => {
			const title = node.querySelector('title');
			if (!title) {
				//console.log('⚠️ Node has no title element');
				return;
			}

			const nodeId = title.textContent.trim();
			//console.log(`🔍 Processing SVG node: "${nodeId}"`);

			// Try node ID first, then fall back to label
			let imageDataUri = nodeImageMap[nodeId];

			if (!imageDataUri) {
				// Try matching by label text
				const textElement = node.querySelector('text');
				if (textElement) {
					const labelText = textElement.textContent.trim();
					imageDataUri = labelImageMap[labelText];
					if (imageDataUri) {
						//console.log(`🖼️ Matched by label "${labelText}" ✅`);
					}
				}
			} else {
				//console.log(`🖼️ Matched by node ID "${nodeId}" ✅`);
			}

			if (!imageDataUri) {
				//console.log('🖼️ No match found ❌');
				//console.log('🔍 Available node IDs:', Object.keys(nodeImageMap));
				//console.log('🔍 Available labels:', Object.keys(labelImageMap));
				return;
			}

			// Get position from text element
			const textElement = node.querySelector('text');
			if (!textElement) {
				//console.log('⚠️ No text element found for', nodeId);
				return;
			}

			const x = parseFloat(textElement.getAttribute('x') || 0);
			const y = parseFloat(textElement.getAttribute('y') || 0);

			//console.log(`📍 Node ${nodeId} at text position x=${x}, y=${y}`);

			// Create and inject image element
			const img = document.createElementNS('http://www.w3.org/2000/svg', 'image');
			img.setAttribute('x', x - 35); // Center the 70px wide image
			img.setAttribute('y', y - 90); // Position well above the text label
			img.setAttribute('width', '70');
			img.setAttribute('height', '70');
			img.setAttribute('href', imageDataUri);

			// Insert the image before other elements
			node.insertBefore(img, node.firstChild);
			injectedCount++;
			//console.log('✅ Injected image for', nodeId, 'at', x, y);
		});

		//console.log(`🎉 Manually injected ${injectedCount} images into SVG`);
		return injectedCount;
	}

	/**
	 * Render a diagram with icons
	 *
	 * Main entry point for rendering a diagram. Fetches icons, generates SVG,
	 * and injects icons into the final output.
	 *
	 * @param {string} chartId - ID of the container element
	 * @param {string} dotContent - Graphviz DOT source code
	 * @param {string} imageMappingJson - JSON string mapping local paths to GitHub URLs
	 */
	async render(chartId, dotContent, imageMappingJson) {
		//console.log('🎨 Rendering diagram for', chartId);

		try {
			const imageMapping = JSON.parse(imageMappingJson);

			// Fetch all images
			const { dataUriCache, failed } = await this.fetchImages(imageMapping);

			// Remove image attributes for viz.js compatibility
			const cleanDot = dotContent.replace(/image="[^"]*"/g, '');
			//console.log('🔧 Removed image attributes for viz.js compatibility');

			// Render base SVG with viz.js
			const svg = this.viz.renderSVGElement(cleanDot);
			//console.log('✅ Base SVG rendered');

			// Create image mappings
			const { nodeImageMap, labelImageMap } = this.createImageMappings(dotContent, dataUriCache);

			// Inject images into SVG
			const injectedCount = this.injectImages(svg, nodeImageMap, labelImageMap);

			// Add to DOM
			const container = document.getElementById(chartId);
			if (!container) {
				console.error(`❌ Container #${chartId} not found`);
				return;
			}

			container.innerHTML = '';

			// Add warning banner if some images failed
			if (failed.length > 0) {
				const warning = document.createElement('div');
				warning.className = 'bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-2 mb-2 text-sm';
				warning.innerHTML = `⚠️ ${failed.length} icon(s) failed to load. Try refreshing or clicking Regenerate.`;
				container.appendChild(warning);
			}

			// Style and append SVG
			svg.removeAttribute('width');
			svg.removeAttribute('height');
			svg.style.width = '100%';
			svg.style.height = 'auto';
			svg.style.maxHeight = '500px';
			container.appendChild(svg);

			// Log summary
			const summary = failed.length > 0
				? `⚠️ ${chartId} rendered with ${injectedCount} images (${failed.length} failed)`
				: `✅ ${chartId} rendered with ${injectedCount} images!`;
			//console.log(summary);

		} catch (error) {
			console.error('Error in render:', error);
			const container = document.getElementById(chartId);
			if (container) {
				container.innerHTML = '<p class="text-red-500">Error: ' + error.message + '</p>';
			}
		}
	}

	/**
	 * Legacy render method without icons (for compatibility)
	 *
	 * @param {string} chartId - ID of the container element
	 * @param {string} dotContent - Graphviz DOT source code
	 */
	renderSimple(chartId, dotContent) {
		//console.log('⚠️ Using legacy renderSimple, images will not load');
		const svg = this.viz.renderSVGElement(dotContent);
		const container = document.getElementById(chartId);
		if (container) {
			container.innerHTML = '';
			svg.style.width = '100%';
			svg.style.height = 'auto';
			container.appendChild(svg);
		}
	}
}
