<script>
	/**
	 * Grokking Network Visualization Component
	 * Optimized for cream backgrounds with clean, high-contrast rendering.
	 * Cloned from NeuralNetworkViz with improved legibility for the anthropic-chic palette.
	 */

	/** @type {{ vizData?: unknown, paused?: boolean }} */
	let { vizData = $bindable(null), paused = false } = $props();

	let canvas = $state(null);
	let ctx = $state(null);
	let animationFrameId = null;
	let pulsePhase = 0;
	let lastDrawTime = 0;

	const TARGET_FPS = 30;
	const FRAME_INTERVAL_MS = 1000 / TARGET_FPS;

	const CANVAS_WIDTH = 1000;
	const NODE_RADIUS = 4;
	const MAX_NODES_PER_LAYER = 150;
	const NEURONS_PER_PILL = 5;

	const canvasHeight = $derived(
		vizData?.layer_sizes?.length
			? Math.max(280, vizData.layer_sizes.length * 110)
			: 280
	);

	const COLORS = {
		background: '#FBF8F3',
		nodeInactive: '#C8BFB4',
		nodeActive: '#306998',
		edgeBase: 'rgba(48, 105, 152, 0.08)',
		edgeActive: '#306998',
		text: '#2C2C2C',
		textMuted: '#6B6560',
		label: '#306998',
		statActive: '#2E7D4F',
		barTrack: '#E5DED5',
		barFill: '#306998',
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
			if (timestamp - lastDrawTime < FRAME_INTERVAL_MS) return;
			lastDrawTime = timestamp;

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

		ctx.fillStyle = COLORS.background;
		ctx.fillRect(0, 0, CANVAS_WIDTH, canvasHeight);

		const layers = vizData.layer_sizes;
		const activations = vizData.activations || [];

		const topPadding = 70;
		const bottomPadding = 70;
		const availableHeight = canvasHeight - topPadding - bottomPadding;
		const spacing = layers.length > 1 ? availableHeight / (layers.length - 1) : 0;

		const layerPositions = layers.map((size, layerIdx) => {
			const y = topPadding + (layerIdx * spacing);
			const PILL_THRESHOLD = 100;
			const usePills = size > PILL_THRESHOLD;
			const pillSize = usePills ? NEURONS_PER_PILL : 1;
			const numPills = Math.ceil(size / pillSize);
			const displaySize = Math.min(numPills, MAX_NODES_PER_LAYER);

			const paddingX = CANVAS_WIDTH * 0.1;
			const availableWidth = CANVAS_WIDTH * 0.8;
			const nodeSpacing = displaySize > 1 ? availableWidth / (displaySize - 1) : 0;
			const startX = paddingX;

			return {
				y, size, displaySize, usePills, pillSize,
				nodes: Array.from({ length: displaySize }, (_, nodeIdx) => {
					const actualIdx = numPills > MAX_NODES_PER_LAYER
						? Math.floor(nodeIdx * (numPills / displaySize))
						: nodeIdx;

					let activation = 0;
					if (usePills) {
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
						activation = activations[layerIdx]?.values?.[actualIdx] || 0;
					}

					return { x: startX + (nodeIdx * nodeSpacing), y, activation, actualIdx };
				})
			};
		});

		// --- EDGES: clean solid lines, no gradient tricks ---
		for (let l = 0; l < layerPositions.length - 1; l++) {
			const fromLayer = layerPositions[l];
			const toLayer = layerPositions[l + 1];
			const maxEdges = 150;
			const fromStep = Math.max(1, Math.ceil(fromLayer.displaySize / Math.sqrt(maxEdges)));
			const toStep = Math.max(1, Math.ceil(toLayer.displaySize / Math.sqrt(maxEdges)));

			let edgeCount = 0;
			for (let i = 0; i < fromLayer.displaySize && edgeCount < maxEdges; i += fromStep) {
				for (let j = 0; j < toLayer.displaySize && edgeCount < maxEdges; j += toStep) {
					const from = fromLayer.nodes[i];
					const to = toLayer.nodes[j];
					const avgActivation = (from.activation + to.activation) / 2;

					// Clean opacity ramp: faint when idle, visible when active
					const opacity = avgActivation > 0.1
						? 0.08 + avgActivation * 0.35
						: 0.04;

					ctx.lineWidth = avgActivation > 0.5 ? 1.2 : 0.5;
					ctx.strokeStyle = `rgba(48, 105, 152, ${opacity})`;
					ctx.beginPath();
					ctx.moveTo(from.x, from.y);
					ctx.lineTo(to.x, to.y);
					ctx.stroke();

					edgeCount++;
				}
			}
		}

		// --- NODES: solid fills, no gradients, clear active/inactive ---
		layerPositions.forEach((layer, layerIdx) => {
			layer.nodes.forEach((node) => {
				const activation = node.activation;
				const isActive = activation > 0.1;

				if (layer.usePills) {
					const pillWidth = 14;
					const pillHeight = NODE_RADIUS * 2;
					const height = isActive ? pillHeight + 1 : pillHeight;
					const cornerRadius = height / 2;

					if (isActive) {
						// Solid active pill
						ctx.fillStyle = COLORS.nodeActive;
						ctx.globalAlpha = 0.3 + activation * 0.7;
					} else {
						// Solid inactive pill
						ctx.fillStyle = COLORS.nodeInactive;
						ctx.globalAlpha = 0.6;
					}

					ctx.beginPath();
					ctx.roundRect(
						node.x - pillWidth / 2,
						node.y - height / 2,
						pillWidth,
						height,
						cornerRadius
					);
					ctx.fill();
					ctx.globalAlpha = 1.0;
				} else {
					const radius = isActive
						? NODE_RADIUS + activation * 1.5
						: NODE_RADIUS;

					if (isActive) {
						// Active: solid accent circle with subtle ring
						ctx.beginPath();
						ctx.arc(node.x, node.y, radius + 3, 0, Math.PI * 2);
						ctx.fillStyle = `rgba(48, 105, 152, ${activation * 0.15})`;
						ctx.fill();

						ctx.beginPath();
						ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
						ctx.fillStyle = COLORS.nodeActive;
						ctx.globalAlpha = 0.4 + activation * 0.6;
						ctx.fill();
						ctx.globalAlpha = 1.0;
					} else {
						// Inactive: solid muted dot
						ctx.beginPath();
						ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
						ctx.fillStyle = COLORS.nodeInactive;
						ctx.globalAlpha = 0.5;
						ctx.fill();
						ctx.globalAlpha = 1.0;
					}
				}
			});

			// --- LABELS ---
			ctx.fillStyle = COLORS.label;
			ctx.font = "13px 'Source Sans 3', sans-serif";
			ctx.textAlign = 'center';

			const layerNames = ['Input', ...Array(layers.length - 2).fill(0).map((_, i) => `Hidden ${i + 1}`), 'Output'];
			const label = layerNames[layerIdx];

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

			const labelY = layer.y - 18;
			ctx.fillText(`${label} (${nodeCount})`, CANVAS_WIDTH / 2, labelY);

			if (activations[layerIdx]) {
				const act = activations[layerIdx];
				ctx.textAlign = 'right';
				ctx.font = "12px 'Source Code Pro', monospace";
				ctx.fillStyle = COLORS.statActive;
				ctx.fillText(
					`Active: ${act.active_count}/${layer.size}`,
					CANVAS_WIDTH - 20,
					labelY
				);
			}
		});

		// --- OUTPUT LABELS (for grokking: 67 classes, no button labels) ---
		// Skip button labels since grokking output is 67 classes, not game buttons
	}

	function drawEmptyState() {
		if (!ctx) return;

		ctx.fillStyle = COLORS.background;
		ctx.fillRect(0, 0, CANVAS_WIDTH, canvasHeight);

		ctx.fillStyle = COLORS.textMuted;
		ctx.font = "14px 'Source Sans 3', sans-serif";
		ctx.textAlign = 'center';
		ctx.fillText('Neural network visualization', CANVAS_WIDTH / 2, canvasHeight / 2 - 10);
		ctx.font = "12px 'Source Sans 3', sans-serif";
		ctx.fillText('Start training to see the network', CANVAS_WIDTH / 2, canvasHeight / 2 + 14);
	}
</script>

<div class="grokking-viz-container">
	<canvas
		bind:this={canvas}
		width={CANVAS_WIDTH}
		height={canvasHeight}
		class="grokking-canvas"
	></canvas>

	{#if vizData && vizData.num_params}
		<div class="viz-info">
			<div class="info-item">
				<span class="info-label">Architecture:</span>
				<span class="info-value">{vizData.layer_sizes.join(' \u2192 ')}</span>
			</div>
			<div class="info-item">
				<span class="info-label">Parameters:</span>
				<span class="info-value">{vizData.num_params.toLocaleString()}</span>
			</div>
			{#if vizData.activations && vizData.activations.length > 0}
				<div class="info-item">
					<span class="info-label">Active Neurons:</span>
					<span class="info-value">
						{vizData.activations.reduce((sum, layer) => sum + layer.active_count, 0)} /
						{vizData.layer_sizes.reduce((sum, size) => sum + size, 0)}
					</span>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.grokking-viz-container {
		background: #FBF8F3;
		border-radius: 8px;
		border: 1px solid #D6CFC5;
		padding: 12px;
		overflow: visible;
		width: 100%;
		box-shadow: 0 1px 3px rgba(0,0,0,0.08);
	}

	.grokking-canvas {
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

	.info-label {
		color: #6B6560;
		font-weight: 600;
	}

	.info-value {
		color: #306998;
	}
</style>
