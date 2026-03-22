<script>
	/**
	 * GrokkingMetricsChart.svelte
	 *
	 * Three-line chart for grokking: Train Acc, Test Acc, Overfit Gap.
	 * Fixed 0-100% Y axis. Overfit gap = train - test (closes at grokking).
	 *
	 * @typedef {Object} GrokMetric
	 * @property {number} epoch
	 * @property {number} trainAcc - 0-100
	 * @property {number} testAcc  - 0-100
	 */

	/** @type {{ metricsHistory: GrokMetric[] }} */
	let { metricsHistory = [] } = $props();

	const WIDTH = 1000;
	const HEIGHT = 280;
	const PAD = { top: 30, right: 20, bottom: 30, left: 45 };
	const chartW = WIDTH - PAD.left - PAD.right;
	const chartH = HEIGHT - PAD.top - PAD.bottom;

	function x(i, len) {
		return PAD.left + (i / Math.max(1, len - 1)) * chartW;
	}
	function y(val) {
		return PAD.top + (1 - val / 100) * chartH;
	}

	function polyline(data, accessor) {
		return data.map((m, i) => `${x(i, data.length)},${y(accessor(m))}`).join(' ');
	}
</script>

<div class="w-full bg-surface rounded-lg p-4 border border-border shadow-card">
	<h3 class="font-heading font-bold text-text-primary mb-3">Grokking Metrics</h3>

	{#if metricsHistory.length > 0}
		{@const latest = metricsHistory[metricsHistory.length - 1]}
		{@const gap = Math.max(0, latest.trainAcc - latest.testAcc)}
		<div class="flex gap-5 mb-2 text-sm font-mono">
			<span style="color: #2E7D4F">Train: {latest.trainAcc.toFixed(1)}%</span>
			<span style="color: #306998">Test: {latest.testAcc.toFixed(1)}%</span>
			<span style="color: #B8860B">Overfit: {gap.toFixed(1)}%</span>
		</div>
	{/if}

	<div class="w-full rounded bg-surface-alt relative" style="height: 280px;">
		{#if metricsHistory.length > 1}
			<svg width="100%" height="100%" viewBox="0 0 {WIDTH} {HEIGHT}" preserveAspectRatio="none" style="display: block;">
				<!-- Grid lines -->
				{#each [0, 25, 50, 75, 100] as pct}
					<line
						x1={PAD.left} y1={y(pct)}
						x2={WIDTH - PAD.right} y2={y(pct)}
						stroke="#D6CFC5" stroke-width="0.5"
					/>
					<text
						x={PAD.left - 6} y={y(pct) + 3}
						font-size="9" font-family="'Source Code Pro', monospace"
						fill="#6B6560" text-anchor="end"
					>{pct}%</text>
				{/each}

				<!-- Epoch axis label -->
				{#if metricsHistory.length > 0}
					{@const first = metricsHistory[0]}
					{@const last = metricsHistory[metricsHistory.length - 1]}
					<text x={PAD.left} y={HEIGHT - 6} font-size="9" font-family="'Source Code Pro', monospace" fill="#6B6560" text-anchor="start">
						{first.epoch}
					</text>
					<text x={WIDTH - PAD.right} y={HEIGHT - 6} font-size="9" font-family="'Source Code Pro', monospace" fill="#6B6560" text-anchor="end">
						{last.epoch}
					</text>
				{/if}

				<!-- Overfit gap fill (area between train and test) -->
				<polygon
					fill="rgba(184, 134, 11, 0.08)"
					points={
						metricsHistory.map((m, i) => `${x(i, metricsHistory.length)},${y(m.trainAcc)}`).join(' ') + ' ' +
						[...metricsHistory].reverse().map((m, i) => `${x(metricsHistory.length - 1 - i, metricsHistory.length)},${y(m.testAcc)}`).join(' ')
					}
				/>

				<!-- Train accuracy (green) -->
				<polyline
					fill="none" stroke="#2E7D4F" stroke-width="2"
					points={polyline(metricsHistory, m => m.trainAcc)}
				/>

				<!-- Test accuracy (accent blue) -->
				<polyline
					fill="none" stroke="#306998" stroke-width="2"
					points={polyline(metricsHistory, m => m.testAcc)}
				/>

				<!-- Overfit gap (amber dashed) -->
				<polyline
					fill="none" stroke="#B8860B" stroke-width="1.5" stroke-dasharray="4,3"
					points={polyline(metricsHistory, m => Math.max(0, m.trainAcc - m.testAcc))}
				/>

				<!-- Legend -->
				<rect x={WIDTH - 170} y={8} width="155" height="52" rx="4" fill="#FBF8F3" stroke="#D6CFC5" stroke-width="0.5" />
				<line x1={WIDTH - 162} y1={22} x2={WIDTH - 142} y2={22} stroke="#2E7D4F" stroke-width="2"/>
				<text x={WIDTH - 137} y={25} font-size="10" font-family="'Source Sans 3', sans-serif" fill="#2C2C2C">Train Accuracy</text>
				<line x1={WIDTH - 162} y1={36} x2={WIDTH - 142} y2={36} stroke="#306998" stroke-width="2"/>
				<text x={WIDTH - 137} y={39} font-size="10" font-family="'Source Sans 3', sans-serif" fill="#2C2C2C">Test Accuracy</text>
				<line x1={WIDTH - 162} y1={50} x2={WIDTH - 142} y2={50} stroke="#B8860B" stroke-width="1.5" stroke-dasharray="4,3"/>
				<text x={WIDTH - 137} y={53} font-size="10" font-family="'Source Sans 3', sans-serif" fill="#2C2C2C">Overfit Gap</text>
			</svg>
		{:else}
			<p class="text-text-muted text-sm flex items-center justify-center h-full">Chart will appear during training</p>
		{/if}
	</div>
</div>
