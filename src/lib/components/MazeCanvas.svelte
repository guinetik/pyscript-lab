<script>
	import { onMount } from 'svelte';

	// Props
	let {
		maze = $bindable(null),
		agentPosition = $bindable({ row: 0, col: 0 }),
		startPosition = $bindable({ row: 0, col: 0 }),
		endPosition = $bindable({ row: 0, col: 0 }),
		qValues = $bindable(null),
		showQValues = $bindable(false),
		cellSize = $bindable(30),
		width = $bindable(450),
		height = $bindable(450)
	} = $props();

	let canvas;
	let ctx;

	onMount(() => {
		ctx = canvas.getContext('2d');
		draw();
	});

	// Reactive redraw - triggers when any visual state changes
	$effect(() => {
		if (ctx && maze) {
			// Access reactive dependencies to trigger redraw
			const _ = [agentPosition, startPosition, endPosition, qValues, showQValues];
			draw();
		}
	});

	function draw() {
		if (!ctx || !maze) return;

		ctx.clearRect(0, 0, width, height);

		// Draw Q-value heatmap if enabled
		if (showQValues && qValues) {
			drawQValueHeatmap();
		}

		// Draw maze walls
		drawMaze();

		// Draw start marker (green circle)
		drawMarker(startPosition, '#00ff00');

		// Draw end marker (red circle)
		drawMarker(endPosition, '#ff0000');

		// Draw agent (blue circle with glow)
		drawAgent(agentPosition);
	}

	function drawMaze() {
		const rows = maze.length;
		const cols = maze[0]?.length || 0;

		ctx.strokeStyle = '#00ff00';
		ctx.lineWidth = 2;

		for (let r = 0; r < rows; r++) {
			for (let c = 0; c < cols; c++) {
				const x = c * cellSize;
				const y = r * cellSize;
				const cell = maze[r][c];

				ctx.beginPath();
				// Draw walls
				if (cell.walls.top) {
					ctx.moveTo(x, y);
					ctx.lineTo(x + cellSize, y);
				}
				if (cell.walls.right) {
					ctx.moveTo(x + cellSize, y);
					ctx.lineTo(x + cellSize, y + cellSize);
				}
				if (cell.walls.bottom) {
					ctx.moveTo(x, y + cellSize);
					ctx.lineTo(x + cellSize, y + cellSize);
				}
				if (cell.walls.left) {
					ctx.moveTo(x, y);
					ctx.lineTo(x, y + cellSize);
				}
				ctx.stroke();
			}
		}
	}

	function drawQValueHeatmap() {
		const rows = maze.length;
		const cols = maze[0]?.length || 0;

		// Find min/max Q-values for normalization
		let minQ = Infinity;
		let maxQ = -Infinity;

		for (let r = 0; r < rows; r++) {
			for (let c = 0; c < cols; c++) {
				const cellQValues = qValues?.[`${r},${c}`];
				if (cellQValues) {
					const maxCellQ = Math.max(...Object.values(cellQValues));
					minQ = Math.min(minQ, maxCellQ);
					maxQ = Math.max(maxQ, maxCellQ);
				}
			}
		}

		// Draw heatmap
		for (let r = 0; r < rows; r++) {
			for (let c = 0; c < cols; c++) {
				const x = c * cellSize;
				const y = r * cellSize;
				const cellQValues = qValues?.[`${r},${c}`];

				if (cellQValues) {
					const maxCellQ = Math.max(...Object.values(cellQValues));
					const normalized = (maxCellQ - minQ) / (maxQ - minQ || 1);

					// Color from dark blue (low) to bright yellow (high)
					const hue = 240 - normalized * 180; // 240 (blue) to 60 (yellow)
					ctx.fillStyle = `hsla(${hue}, 80%, 50%, 0.3)`;
					ctx.fillRect(x + 2, y + 2, cellSize - 4, cellSize - 4);
				}
			}
		}
	}

	function drawMarker(position, color) {
		const x = position.col * cellSize + cellSize / 2;
		const y = position.row * cellSize + cellSize / 2;
		const radius = cellSize / 3;

		ctx.fillStyle = color;
		ctx.beginPath();
		ctx.arc(x, y, radius, 0, Math.PI * 2);
		ctx.fill();
	}

	function drawAgent(position) {
		const x = position.col * cellSize + cellSize / 2;
		const y = position.row * cellSize + cellSize / 2;
		const radius = cellSize / 3.5;

		// Glow effect
		ctx.shadowBlur = 10;
		ctx.shadowColor = '#00aaff';

		ctx.fillStyle = '#00aaff';
		ctx.beginPath();
		ctx.arc(x, y, radius, 0, Math.PI * 2);
		ctx.fill();

		// Reset shadow
		ctx.shadowBlur = 0;
	}
</script>

<div class="maze-container">
	<canvas bind:this={canvas} {width} {height} class="maze-canvas"></canvas>
</div>

<style>
	.maze-container {
		display: flex;
		justify-content: center;
		align-items: center;
		padding: 1rem;
	}

	.maze-canvas {
		border: 2px solid #444;
		background: #000;
		border-radius: 4px;
	}
</style>
