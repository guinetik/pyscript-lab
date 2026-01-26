<script>
	/**
	 * MetricsChart.svelte
	 * 
	 * Visualizes training metrics over generations/epochs.
	 * 
	 * @typedef {Object} Metric
	 * @property {number} gen - Generation/epoch number
	 * @property {number} fitness - Primary metric (fitness, train accuracy, etc.)
	 * @property {number} distance - Secondary metric (distance, test accuracy, etc.)
	 */
	
	/** @type {{ metricsHistory: Metric[], label1?: string, label2?: string }} */
	let { 
		metricsHistory = [],
		label1 = 'Fitness',
		label2 = 'Distance'
	} = $props();
</script>

<div class="w-full bg-white rounded-lg p-4 border-2 border-gray-300">
	<h3 class="font-bold mb-3">📈 Training Metrics</h3>
	<div id="metrics-chart" class="w-full h-64 bg-gray-50 rounded relative">
		{#if metricsHistory.length > 1}
			{@const maxFit = Math.max(...metricsHistory.map(m => m.fitness)) || 1}
			{@const maxDist = Math.max(...metricsHistory.map(m => m.distance)) || 1}
			{@const width = 1000}
			{@const height = 250}
			{@const padding = 50}
			<svg width="100%" height="100%" viewBox="0 0 {width} {height}" preserveAspectRatio="none" style="display: block;">
				<!-- Grid lines -->
				{#each [0, 0.25, 0.5, 0.75, 1] as y}
					<line 
						x1={padding} y1={padding + (1-y) * (height - 2*padding)} 
						x2={width - padding} y2={padding + (1-y) * (height - 2*padding)} 
						stroke="#e5e7eb" stroke-width="1" />
				{/each}
				
				<!-- Fitness line (green) -->
				<polyline
					fill="none"
					stroke="#22c55e"
					stroke-width="2"
					points={metricsHistory.map((m, i) => {
						const x = padding + (i / (metricsHistory.length - 1)) * (width - 2*padding);
						const y = padding + (1 - m.fitness / maxFit) * (height - 2*padding);
						return `${x},${y}`;
					}).join(' ')}
				/>
				
				<!-- Distance line (blue) -->
				<polyline
					fill="none"
					stroke="#3b82f6"
					stroke-width="2"
					points={metricsHistory.map((m, i) => {
						const x = padding + (i / (metricsHistory.length - 1)) * (width - 2*padding);
						const y = padding + (1 - m.distance / maxDist) * (height - 2*padding);
						return `${x},${y}`;
					}).join(' ')}
				/>
				
				<!-- Legend -->
				<rect x={width - 115} y={10} width="105" height="42" fill="white" stroke="#e5e7eb" rx="4"/>
				<line x1={width - 107} y1={24} x2={width - 87} y2={24} stroke="#22c55e" stroke-width="2"/>
				<text x={width - 82} y={28} font-size="11" fill="#374151">{label1}</text>
				<line x1={width - 107} y1={40} x2={width - 87} y2={40} stroke="#3b82f6" stroke-width="2"/>
				<text x={width - 82} y={44} font-size="11" fill="#374151">{label2}</text>
			</svg>
		{:else}
			<p class="text-gray-400 text-sm flex items-center justify-center h-full">Chart will appear during Training</p>
		{/if}
	</div>
</div>