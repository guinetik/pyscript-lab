<script>
	/**
	 * Neural Network Visualization Component
	 * Renders a visual representation of the neural network with live activations
	 */

	// Props
	let { vizData = $bindable(null) } = $props();

	// Local state
	let canvas = $state(null);
	let ctx = $state(null);
	let animationFrameId = null; // Not reactive state

	// Animation state (not reactive - used only in animation loop)
	let pulsePhase = 0;

	// Layout constants - HORIZONTAL LAYOUT (rows not columns)
	const CANVAS_WIDTH = 1000;
	const LAYER_SPACING = 120; // Vertical spacing between rows
	const NODE_RADIUS = 3;
	const MAX_NODES_PER_LAYER = 150; // Show all nodes
	const NEURONS_PER_PILL = 5; // Group neurons into pills (hidden layers only)

	// Dynamic height based on number of layers (fluid layout)
	const canvasHeight = $derived(
		vizData?.layer_sizes?.length
			? 70 + (vizData.layer_sizes.length * LAYER_SPACING) + 90 // Extra space for output labels/bars
			: 400 // Default height for empty state
	);

	// Color scheme
	const COLORS = {
		background: '#0f172a',
		node: '#64748b',
		nodeActive: '#22d3ee',
		edge: '#334155',
		edgeActive: '#06b6d4',
		text: '#cbd5e1'
	};

	$effect(() => {
		if (canvas) {
			ctx = canvas.getContext('2d');
			startAnimation();
		}

		return () => {
			if (animationFrameId) {
				cancelAnimationFrame(animationFrameId);
			}
		};
	});

	function startAnimation() {
		function animate() {
			pulsePhase = (pulsePhase + 0.01) % (Math.PI * 2); // Slower pulse
			drawNetwork();
			animationFrameId = requestAnimationFrame(animate);
		}
		animate();
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

		// Debug: log activation data structure
		if (activations.length > 0 && !window._loggedActivations) {
			const outputAct = activations[layers.length - 1];
			console.log('🔍 Activation data:', {
				hasActivations: activations.length > 0,
				numLayers: layers.length,
				numActivations: activations.length,
				outputLayerActivation: outputAct,
				outputHasValues: !!outputAct?.values,
				outputValuesType: typeof outputAct?.values,
				outputValuesIsArray: Array.isArray(outputAct?.values),
				outputValuesLength: outputAct?.values?.length,
				outputValues: outputAct?.values,
				firstValue: outputAct?.values?.[0],
				allActivations: activations
			});
			window._loggedActivations = true;
		}

		// Calculate node positions for each layer - HORIZONTAL LAYOUT
		const layerPositions = layers.map((size, layerIdx) => {
			const y = 70 + layerIdx * LAYER_SPACING; // Vertical position (row)

			// Determine if this is a hidden layer (for pill grouping)
			const isHidden = layerIdx > 0 && layerIdx < layers.length - 1;

			// Only use pills if hidden layer has more than MAX_NODES_PER_LAYER neurons
			const usePills = isHidden && size > MAX_NODES_PER_LAYER;
			const pillSize = usePills ? NEURONS_PER_PILL : 1;
			const numPills = Math.ceil(size / pillSize);
			const displaySize = Math.min(numPills, MAX_NODES_PER_LAYER);

			// Calculate horizontal spacing to fit all nodes/pills with padding
			const paddingX = 120; // More space for labels
			const paddingRight = 120; // More space for active count
			const availableWidth = CANVAS_WIDTH - paddingX - paddingRight;
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

					// Debug output layer node creation
					if (!window._loggedNodeCreation && layerIdx === layers.length - 1 && nodeIdx < 6) {
						console.log(`🔍 Creating output node ${nodeIdx}:`, {
							layerIdx,
							nodeIdx,
							actualIdx,
							hasActivations: !!activations[layerIdx],
							activationValue: activation,
							valuesArray: activations[layerIdx]?.values
						});
						if (nodeIdx === 5) window._loggedNodeCreation = true;
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

					ctx.strokeStyle = `rgba(255, 255, 255, ${opacity})`;
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

				// Draw pills for hidden layers, circles for input/output
				if (layer.usePills) {
					// Pill dimensions
					const pillWidth = 14; // Wider pills
					const pillHeight = NODE_RADIUS * 2;
					const pulse = Math.sin(pulsePhase) * 0.5;
					const height = isActive
						? pillHeight + pulse + (activation * 0.5)
						: pillHeight;
					const cornerRadius = height / 2; // Fully rounded ends

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
						gradient.addColorStop(0, '#4a5a6a');
						gradient.addColorStop(0.5, '#7a8a9a');
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
					// Regular circular nodes for input/output layers
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
						gradient.addColorStop(0, '#7a8a9a');
						gradient.addColorStop(1, '#4a5a6a');
						ctx.fillStyle = gradient;
						ctx.beginPath();
						ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
						ctx.fill();
					}
				}
			});

			// Layer labels - centered above each row
			ctx.fillStyle = COLORS.text;
			ctx.font = '13px monospace';
			ctx.textAlign = 'center';

			const layerNames = ['Input', ...Array(layers.length - 2).fill(0).map((_, i) => `Hidden ${i + 1}`), 'Output'];
			const label = layerNames[layerIdx];

			// Show pill count for hidden layers, node count otherwise
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

			// Draw label centered at top of canvas, above the layer row
			ctx.fillText(`${label} (${nodeCount})`, CANVAS_WIDTH / 2, layer.y - 10);

			// Show activation stats if available - on the right side
			if (activations[layerIdx]) {
				const act = activations[layerIdx];
				ctx.textAlign = 'right';
				ctx.font = '12px monospace';
				ctx.fillStyle = '#22d3ee'; // Bright cyan for visibility
				ctx.fillText(
					`Active: ${act.active_count}/${layer.size}`,
					CANVAS_WIDTH - 20,
					layer.y - 10
				);
			}
		});

		// Draw button labels for output layer - horizontal layout below output nodes
		if (layers.length > 0) {
			const outputLayer = layerPositions[layerPositions.length - 1];
			const buttons = ['UP', 'DOWN', 'LEFT', 'RIGHT', 'A', 'B'];

			ctx.font = '11px monospace';
			ctx.textAlign = 'center';

			// Only show if output layer has 6 nodes (button output)
			if (outputLayer.size === 6) {
				// Debug output layer activations once
				if (!window._loggedOutputActivations && activations.length > 0) {
					console.log('🎮 Output layer activations:', {
						layerIdx: layers.length - 1,
						nodes: outputLayer.nodes.map((n, i) => ({
							button: buttons[i],
							activation: n.activation,
							actualIdx: n.actualIdx
						})),
						rawActivationData: activations[layers.length - 1]
					});
					window._loggedOutputActivations = true;
				}

				outputLayer.nodes.forEach((node, idx) => {
					if (idx < buttons.length) {
						const activation = node.activation || 0;

						// Debug log ALL button activation values
						if (!window._loggedButtonActivation) {
							console.log('🔍 Button activation debug:', {
								buttonIndex: idx,
								button: buttons[idx],
								nodeActivation: node.activation,
								actualIdx: node.actualIdx,
								outputLayerIdx: layers.length - 1,
								hasActivations: !!activations[layers.length - 1],
								activationObject: activations[layers.length - 1],
								allValues: activations[layers.length - 1]?.values,
								valueAtIndex: activations[layers.length - 1]?.values?.[idx]
							});
							if (idx === buttons.length - 1) {
								window._loggedButtonActivation = true;
							}
						}

						// Button label above node
						ctx.fillStyle = activation > 0.5 ? '#ffffff' : COLORS.text;
						ctx.fillText(buttons[idx], node.x, node.y - 15);

						// Percentage below node
						ctx.font = '12px monospace';
						ctx.fillStyle = activation > 0.1 ? '#ffffff' : '#94a3b8';
						ctx.fillText(`${(activation * 100).toFixed(0)}%`, node.x, node.y + 22);
						ctx.font = '11px monospace';

						// Draw activation bar below percentage
						const barWidth = 50;
						const barHeight = 5;
						ctx.fillStyle = 'rgba(100, 116, 139, 0.4)';
						ctx.fillRect(node.x - barWidth/2, node.y + 28, barWidth, barHeight);

						ctx.fillStyle = activation > 0.5 ? '#ffffff' : COLORS.edgeActive;
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
		ctx.fillStyle = '#64748b';
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
		background: #0f172a;
		border-radius: 8px;
		border: 2px solid #1e293b;
		padding: 12px;
		overflow: visible;
		width: 100%;
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
		background: #1e293b;
		border-radius: 4px;
		font-family: monospace;
		font-size: 12px;
	}

	.info-item {
		display: flex;
		gap: 6px;
	}

	.label {
		color: #94a3b8;
		font-weight: 600;
	}

	.value {
		color: #22d3ee;
	}
</style>
