<script>
	/**
	 * Neural Network Visualization Component
	 * Renders a visual representation of the neural network with live activations
	 */

	/**
	 * @typedef {Object} NeuralNetworkVizProps
	 * @property {unknown} [vizData]
	 * @property {boolean} [paused] When true, no rAF — single `drawNetwork`. During headless training pass a **stable** frozen snapshot so `vizData` identity does not change every tick (see neuro `+page.svelte`).
	 */
	/** @type {NeuralNetworkVizProps} */
	let { vizData = $bindable(null), paused = false } = $props();

	// Local state
	let canvas = $state(null);
	let ctx = $state(null);
	let animationFrameId = null; // Not reactive state

	// Animation state (not reactive - used only in animation loop)
	let pulsePhase = 0;
	let lastDrawTime = 0;

	// Throttle: 30fps to reduce main-thread load (was 60fps)
	const TARGET_FPS = 30;
	const FRAME_INTERVAL_MS = 1000 / TARGET_FPS;

	// Layout constants - HORIZONTAL LAYOUT (rows not columns)
	const CANVAS_WIDTH = 1000;
	const NODE_RADIUS = 3;
	const MAX_NODES_PER_LAYER = 150; // Show all nodes
	const NEURONS_PER_PILL = 5; // Group neurons into pills for performance

	// Dynamic layout calculations
	const canvasHeight = $derived(
		vizData?.layer_sizes?.length
			? Math.max(280, vizData.layer_sizes.length * 110) // Balanced height
			: 280
	);

	// Dynamic spacing based on number of layers
	const layerSpacing = $derived(
		vizData?.layer_sizes?.length
			? (canvasHeight - 140) / Math.max(1, vizData.layer_sizes.length - 1) // Distribute evenly
			: 120
	);

	// Color scheme
	const COLORS = {
		background: '#FBF8F3',
		node: '#D6CFC5',
		nodeActive: '#2E7D4F',
		edge: '#D6CFC5',
		edgeActive: '#306998',
		text: '#2C2C2C'
	};

	$effect(() => {
		void paused;
		if (!canvas) return;
		ctx = canvas.getContext('2d');

		const hasData = vizData && vizData.layer_sizes;

		if (!hasData) {
			stopAnimation();
			drawEmptyState();
			return;
		}

		if (paused) {
			stopAnimation();
			drawNetwork();
		} else {
			startAnimation();
		}

		return () => stopAnimation();
	});

	function stopAnimation() {
		if (animationFrameId) {
			cancelAnimationFrame(animationFrameId);
			animationFrameId = null;
		}
	}

	function startAnimation() {
		stopAnimation();
		lastDrawTime = 0;

		function animate(timestamp) {
			animationFrameId = requestAnimationFrame(animate);

			// Throttle to TARGET_FPS - skip frame if too soon
			if (timestamp - lastDrawTime < FRAME_INTERVAL_MS) return;
			lastDrawTime = timestamp;

			// Pause if vizData was cleared (e.g. training reset)
			if (!vizData || !vizData.layer_sizes) {
				drawEmptyState();
				return;
			}

			pulsePhase = (pulsePhase + 0.01) % (Math.PI * 2);
			drawNetwork();
		}

		animationFrameId = requestAnimationFrame(animate);
	}

	function drawNetwork() {
		if (!ctx || !vizData || !vizData.layer_sizes) {
			drawEmptyState();
			return;
		}

		// Clear canvas
		ctx.fillStyle = COLORS.background;
		ctx.fillRect(0, 0, CANVAS_WIDTH, canvasHeight);

		const layers = vizData.layer_sizes;
		const activations = vizData.activations || [];

		// Calculate dynamic vertical spacing
		const topPadding = 70;
		const bottomPadding = 70;
		const availableHeight = canvasHeight - topPadding - bottomPadding;
		const spacing = layers.length > 1 ? availableHeight / (layers.length - 1) : 0;

		// Calculate node positions for each layer - FLUID HORIZONTAL LAYOUT
		const layerPositions = layers.map((size, layerIdx) => {
			// Dynamic vertical position - evenly distributed
			const y = topPadding + (layerIdx * spacing);

			// Use pills for any layer with more than 100 neurons (for performance)
			const PILL_THRESHOLD = 100;
			const usePills = size > PILL_THRESHOLD;
			const pillSize = usePills ? NEURONS_PER_PILL : 1;
			const numPills = Math.ceil(size / pillSize);
			const displaySize = Math.min(numPills, MAX_NODES_PER_LAYER);

			// Dynamic horizontal spacing - use 80% of canvas width
			const paddingX = CANVAS_WIDTH * 0.1; // 10% padding on each side
			const availableWidth = CANVAS_WIDTH * 0.8; // 80% usable width
			const nodeSpacing = displaySize > 1 ? availableWidth / (displaySize - 1) : 0;
			const startX = paddingX;

			return {
				y,
				size,
				displaySize,
				usePills,
				pillSize,
				nodes: Array.from({ length: displaySize }, (_, nodeIdx) => {
					// If we're sampling, calculate which actual node/pill this represents
					const actualIdx = numPills > MAX_NODES_PER_LAYER
						? Math.floor(nodeIdx * (numPills / displaySize))
						: nodeIdx;

					// For pills, calculate average activation across the group
					let activation = 0;
					if (usePills) {
						// Average activation of neurons in this pill
						const startNeuron = actualIdx * pillSize;
						const endNeuron = Math.min(startNeuron + pillSize, size);
						let sum = 0;
						let count = 0;
						for (let i = startNeuron; i < endNeuron; i++) {
							sum += activations[layerIdx]?.values?.[i] || 0;
							count++;
						}
						activation = count > 0 ? sum / count : 0;
					} else {
						// Regular neuron activation
						activation = activations[layerIdx]?.values?.[actualIdx] || 0;
					}

					return {
						x: startX + (nodeIdx * nodeSpacing),
						y,
						activation,
						actualIdx
					};
				})
			};
		});

		// Draw edges between layers
		for (let l = 0; l < layerPositions.length - 1; l++) {
			const fromLayer = layerPositions[l];
			const toLayer = layerPositions[l + 1];

			// Draw a subset of edges (would be too dense otherwise)
			const maxEdges = 150;

			// Calculate step sizes for sampling nodes intelligently
			const totalPossibleEdges = fromLayer.displaySize * toLayer.displaySize;
			const sampleRatio = Math.min(1.0, maxEdges / totalPossibleEdges);

			// Sample from nodes evenly
			const fromStep = Math.max(1, Math.ceil(fromLayer.displaySize / Math.sqrt(maxEdges)));
			const toStep = Math.max(1, Math.ceil(toLayer.displaySize / Math.sqrt(maxEdges)));

			let edgeCount = 0;
			for (let i = 0; i < fromLayer.displaySize && edgeCount < maxEdges; i += fromStep) {
				for (let j = 0; j < toLayer.displaySize && edgeCount < maxEdges; j += toStep) {
					const from = fromLayer.nodes[i];
					const to = toLayer.nodes[j];

					// Edge opacity based on both nodes' activation (more subtle)
					let opacity;
					if (activations.length > 0) {
						const avgActivation = (from.activation + to.activation) / 2;
						// Subtler edge visibility
						opacity = 0.03 + (avgActivation * 0.2);
					} else {
						opacity = 0.05; // Reduced default visibility
					}

					// Dynamic line width based on activation (more subtle)
					const avgActivation = (from.activation + to.activation) / 2;
					ctx.lineWidth = avgActivation > 0.5 ? 1.0 : 0.4;

					ctx.strokeStyle = `rgba(48, 105, 152, ${opacity})`;
					ctx.beginPath();
					ctx.moveTo(from.x, from.y);
					ctx.lineTo(to.x, to.y);
					ctx.stroke();

					edgeCount++;
				}
			}
		}

		// Draw nodes
		layerPositions.forEach((layer, layerIdx) => {
			layer.nodes.forEach((node, nodeIdx) => {
				const activation = node.activation;
				const isActive = activation > 0.1;

				// Draw pills for layers with >100 neurons, circles otherwise
				if (layer.usePills) {
					// Pill dimensions
					const pillWidth = 14;
					const pillHeight = NODE_RADIUS * 2;
					const pulse = Math.sin(pulsePhase) * 0.5;
					const height = isActive
						? pillHeight + pulse + (activation * 0.5)
						: pillHeight;
					const cornerRadius = height / 2;

					if (isActive) {
						// Outer glow for active pills
						const glowPadding = 3;
						ctx.fillStyle = `rgba(100, 200, 255, ${activation * 0.15})`;
						ctx.beginPath();
						ctx.roundRect(
							node.x - pillWidth/2 - glowPadding,
							node.y - height/2 - glowPadding,
							pillWidth + glowPadding * 2,
							height + glowPadding * 2,
							cornerRadius + glowPadding
						);
						ctx.fill();

						// Inner bright pill
						const gradient = ctx.createLinearGradient(
							node.x - pillWidth/2, node.y,
							node.x + pillWidth/2, node.y
						);
						gradient.addColorStop(0, `rgba(150, 180, 220, ${activation * 0.8})`);
						gradient.addColorStop(0.5, `rgba(200, 220, 255, ${activation})`);
						gradient.addColorStop(1, `rgba(150, 180, 220, ${activation * 0.8})`);
						ctx.fillStyle = gradient;
					} else {
						// Inactive pill
						const gradient = ctx.createLinearGradient(
							node.x - pillWidth/2, node.y,
							node.x + pillWidth/2, node.y
						);
						gradient.addColorStop(0, '#D6CFC5');
						gradient.addColorStop(0.5, '#B5ADA4');
						gradient.addColorStop(1, '#4a5a6a');
						ctx.fillStyle = gradient;
					}

					ctx.beginPath();
					ctx.roundRect(
						node.x - pillWidth/2,
						node.y - height/2,
						pillWidth,
						height,
						cornerRadius
					);
					ctx.fill();
				} else {
					// Regular circular nodes for layers with <=100 neurons
					const baseRadius = NODE_RADIUS;
					const pulse = Math.sin(pulsePhase) * 0.5;
					const radius = isActive
						? baseRadius + pulse + (activation * 0.5)
						: baseRadius;

					if (isActive) {
						// Outer glow for active nodes
						const glowRadius = radius * 2;
						const glow = ctx.createRadialGradient(
							node.x, node.y, 0,
							node.x, node.y, glowRadius
						);
						glow.addColorStop(0, `rgba(255, 255, 255, ${activation * 0.3})`);
						glow.addColorStop(0.5, `rgba(100, 200, 255, ${activation * 0.1})`);
						glow.addColorStop(1, 'rgba(255, 255, 255, 0)');
						ctx.fillStyle = glow;
						ctx.beginPath();
						ctx.arc(node.x, node.y, glowRadius, 0, Math.PI * 2);
						ctx.fill();

						// Inner bright node
						const innerGradient = ctx.createRadialGradient(
							node.x, node.y, 0,
							node.x, node.y, radius
						);
						innerGradient.addColorStop(0, `rgba(255, 255, 255, ${activation})`);
						innerGradient.addColorStop(0.7, `rgba(200, 220, 255, ${activation * 0.8})`);
						innerGradient.addColorStop(1, `rgba(150, 180, 220, ${activation * 0.6})`);
						ctx.fillStyle = innerGradient;
						ctx.beginPath();
						ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
						ctx.fill();
					} else {
						// Inactive node
						const gradient = ctx.createRadialGradient(
							node.x, node.y, 0,
							node.x, node.y, radius
						);
						gradient.addColorStop(0, '#B5ADA4');
						gradient.addColorStop(1, '#4a5a6a');
						ctx.fillStyle = gradient;
						ctx.beginPath();
						ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
						ctx.fill();
					}
				}
			});

			// Layer labels - positioned dynamically above each row
			ctx.fillStyle = COLORS.text;
			ctx.font = '13px monospace';
			ctx.textAlign = 'center';

			const layerNames = ['Input', ...Array(layers.length - 2).fill(0).map((_, i) => `Hidden ${i + 1}`), 'Output'];
			const label = layerNames[layerIdx];

			// Show pill count for layers using pills, node count otherwise
			let nodeCount;
			if (layer.usePills) {
				const numPills = Math.ceil(layer.size / layer.pillSize);
				nodeCount = numPills > MAX_NODES_PER_LAYER
					? `${layer.size} Neurons (${layer.displaySize}/${numPills} pills)`
					: `${layer.size} Neurons (${numPills} pills)`;
			} else {
				nodeCount = layer.size > MAX_NODES_PER_LAYER
					? `${layer.size} Neurons (${layer.displaySize} shown)`
					: `${layer.size} Neurons`;
			}

			// Draw label centered horizontally, above the layer row
			const labelY = layer.y - 15; // Positioned above nodes
			ctx.fillStyle = '#306998';
			ctx.fillText(`${label} (${nodeCount})`, CANVAS_WIDTH / 2, labelY);

			// Show activation stats if available - on the right side, aligned with label
			if (activations[layerIdx]) {
				const act = activations[layerIdx];
				ctx.textAlign = 'right';
				ctx.font = '12px monospace';
				ctx.fillStyle = '#2E7D4F';
				ctx.fillText(
					`Active: ${act.active_count}/${layer.size}`,
					CANVAS_WIDTH - 20,
					labelY
				);
			}
		});

		// Draw button labels for output layer - horizontal layout below output nodes
		if (layers.length > 0) {
			const outputLayer = layerPositions[layerPositions.length - 1];

			// Determine button labels based on output size
			let buttons = [];
			if (outputLayer.size === 4) {
				// 4-button mode: [LEFT, RIGHT, A, B]
				buttons = ['LEFT', 'RIGHT', 'A', 'B'];
			} else if (outputLayer.size === 6) {
				// 6-button mode: [UP, DOWN, LEFT, RIGHT, A, B]
				buttons = ['UP', 'DOWN', 'LEFT', 'RIGHT', 'A', 'B'];
			}

			// Only show button labels if we recognized the output size (4 or 6)
			if (buttons.length > 0) {
				ctx.font = '11px monospace';
				ctx.textAlign = 'center';

				outputLayer.nodes.forEach((node, idx) => {
					if (idx < buttons.length) {
						const activation = node.activation || 0;

						// Button label above node
						ctx.fillStyle = activation > 0.5 ? '#306998' : COLORS.text;
						ctx.fillText(buttons[idx], node.x, node.y - 15);

						// Percentage below node
						ctx.font = '12px monospace';
						ctx.fillStyle = activation > 0.1 ? '#2C2C2C' : '#6B6560';
						ctx.fillText(`${(activation * 100).toFixed(0)}%`, node.x, node.y + 22);
						ctx.font = '11px monospace';

						// Draw activation bar below percentage
						const barWidth = 50;
						const barHeight = 5;
						ctx.fillStyle = 'rgba(214, 207, 197, 0.6)';
						ctx.fillRect(node.x - barWidth/2, node.y + 28, barWidth, barHeight);

						ctx.fillStyle = COLORS.edgeActive;
						ctx.fillRect(node.x - barWidth/2, node.y + 28, barWidth * activation, barHeight);
					}
				});
			}
		}
	}

	function drawEmptyState() {
		if (!ctx) return;

		ctx.fillStyle = COLORS.background;
		ctx.fillRect(0, 0, CANVAS_WIDTH, canvasHeight);

		ctx.fillStyle = COLORS.text;
		ctx.font = '14px monospace';
		ctx.textAlign = 'center';
		ctx.fillText('Neural network visualization', CANVAS_WIDTH / 2, canvasHeight / 2 - 20);
		ctx.font = '12px monospace';
		ctx.fillStyle = '#6B6560';
		ctx.fillText('Enable with: toggleNetworkVisualization(true)', CANVAS_WIDTH / 2, canvasHeight / 2 + 10);
	}
</script>

<div class="neural-viz-container">
	<canvas
		bind:this={canvas}
		width={CANVAS_WIDTH}
		height={canvasHeight}
		class="neural-canvas"
	></canvas>

	{#if vizData && vizData.num_params}
		<div class="viz-info">
			<div class="info-item">
				<span class="label">Architecture:</span>
				<span class="value">{vizData.layer_sizes.join(' → ')}</span>
			</div>
			<div class="info-item">
				<span class="label">Parameters:</span>
				<span class="value">{vizData.num_params.toLocaleString()}</span>
			</div>
			{#if vizData.activations && vizData.activations.length > 0}
				<div class="info-item">
					<span class="label">Active Neurons:</span>
					<span class="value">
						{vizData.activations.reduce((sum, layer) => sum + layer.active_count, 0)} /
						{vizData.layer_sizes.reduce((sum, size) => sum + size, 0)}
					</span>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.neural-viz-container {
		background: #FBF8F3;
		border-radius: 8px;
		border: 1px solid #D6CFC5;
		padding: 12px;
		overflow: visible;
		width: 100%;
		box-shadow: 0 1px 3px rgba(0,0,0,0.08);
	}

	.neural-canvas {
		display: block;
		width: 100%;
		height: auto;
		border-radius: 4px;
	}

	.viz-info {
		display: flex;
		gap: 16px;
		margin-top: 12px;
		padding: 8px;
		background: #F3EDE4;
		border-radius: 4px;
		font-family: 'Source Code Pro', monospace;
		font-size: 12px;
	}

	.info-item {
		display: flex;
		gap: 6px;
	}

	.label {
		color: #6B6560;
		font-weight: 600;
	}

	.value {
		color: #306998;
	}
</style>