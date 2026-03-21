<script>
	/**
	 * Breeding overview: canvas genetic-flow art + compact champion-only table.
	 *
	 * @typedef {Object} BreedingEvent
	 * @property {number} slot
	 * @property {string} mode
	 * @property {string} operator
	 * @property {number[]} parent_slots
	 * @property {boolean} preserved
	 * @property {boolean} mutated
	 * @property {number} mutation_rate
	 * @property {number} mutation_strength
	 *
	 * @typedef {Object} BreedingData
	 * @property {number} generation
	 * @property {string} mode
	 * @property {BreedingEvent[]} events
	 */

	import BreedingGenArt from '$lib/components/BreedingGenArt.svelte';

	/** @type {{ breedingData?: BreedingData | null }} */
	let { breedingData = null } = $props();

	/**
	 * @param {string} value
	 * @returns {string}
	 */
	function prettyLabel(value) {
		const labels = {
			simple: 'Simple',
			sbx: 'SBX',
			uniform: 'Uniform',
			optimize: 'Optimize',
			mutation: 'Mutation',
			preserve: 'Champion'
		};
		return labels[value] ?? value;
	}

	/**
	 * @param {string} operator
	 * @returns {{ badge: string, row: string, dot: string }}
	 */
	function operatorTheme(operator) {
		switch (operator) {
			case 'preserve':
				return {
					badge: 'bg-amber-100 text-amber-800 border-amber-300',
					row: 'bg-amber-50',
					dot: 'bg-amber-500'
				};
			case 'sbx':
				return {
					badge: 'bg-sky-100 text-sky-800 border-sky-300',
					row: 'bg-sky-50',
					dot: 'bg-sky-500'
				};
			case 'uniform':
				return {
					badge: 'bg-fuchsia-100 text-fuchsia-800 border-fuchsia-300',
					row: 'bg-fuchsia-50',
					dot: 'bg-fuchsia-500'
				};
			default:
				return {
					badge: 'bg-emerald-100 text-emerald-800 border-emerald-300',
					row: 'bg-emerald-50',
					dot: 'bg-emerald-500'
				};
		}
	}

	const events = $derived(breedingData?.events ?? []);
	/** Slots carried unchanged (elites / champion) — table shows only these. */
	const championEvents = $derived(events.filter((event) => event.preserved === true));
	const preservedCount = $derived(events.filter((event) => event.preserved).length);
	const bredCount = $derived(events.filter((event) => !event.preserved).length);
	const mutatedCount = $derived(events.filter((event) => event.mutated).length);
	const uniqueParents = $derived(
		new Set(events.flatMap((event) => event.parent_slots ?? []).filter((slot) => slot >= 0)).size
	);
</script>

<div class="rounded-2xl border border-border bg-surface p-3 text-text-primary shadow-card">
	<div class="mb-3 flex flex-wrap items-start justify-between gap-3">
		<div>
			<p class="text-[11px] font-semibold uppercase tracking-[0.3em] text-accent">Breeding Lineage</p>
			<h3 class="mt-1 text-lg font-heading font-black tracking-tight text-text-primary">
				Generation {breedingData?.generation ?? '...'}
			</h3>
			<p class="mt-1 max-w-2xl text-xs text-text-muted">
				<strong class="text-accent">Particle helix:</strong> paired dots per slot in a real rotating 3D projection; colors = operator. Not the neural net graph. Table =
				<strong class="text-text-primary font-semibold">preserved</strong> slots only.
			</p>
		</div>
		{#if breedingData}
			<div class="inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-accent">
				<span class="h-2 w-2 rounded-full bg-accent"></span>
				{prettyLabel(breedingData.mode)}
			</div>
		{/if}
	</div>

	{#if breedingData && events.length > 0}
		<div class="flex flex-col md:flex-row gap-3">
			<!-- Left: Helix canvas -->
			<div class="md:w-1/2 flex-shrink-0">
				<BreedingGenArt breedingData={breedingData} />
				<div class="mt-2 rounded-lg border border-border bg-callout px-3 py-2 text-[11px] leading-relaxed text-text-primary">
					<p class="font-semibold text-accent">How to read the helix</p>
					<p class="mt-1">
						Each step = one population slot. Dot color = operator:
						<span class="whitespace-nowrap text-amber-600">Champion</span>
						<span class="mx-0.5 text-text-muted">·</span>
						<span class="whitespace-nowrap text-sky-600">SBX</span>
						<span class="mx-0.5 text-text-muted">·</span>
						<span class="whitespace-nowrap text-fuchsia-600">Uniform</span>
						<span class="mx-0.5 text-text-muted">·</span>
						<span class="whitespace-nowrap text-emerald-600">Mutation</span>
					</p>
				</div>
			</div>

			<!-- Right: Stats -->
			<div class="md:w-1/2 flex flex-col gap-2">
				<div class="grid grid-cols-2 gap-2">
					<div class="rounded-lg border border-border bg-surface-alt p-2.5">
						<div class="text-[11px] uppercase tracking-[0.25em] text-text-muted">Events</div>
						<div class="mt-1 text-xl font-black text-text-primary">{events.length}</div>
					</div>
					<div class="rounded-lg border border-border bg-surface-alt p-2.5">
						<div class="text-[11px] uppercase tracking-[0.25em] text-text-muted">Preserved</div>
						<div class="mt-1 text-xl font-black text-accent">{preservedCount}</div>
					</div>
					<div class="rounded-lg border border-border bg-surface-alt p-2.5">
						<div class="text-[11px] uppercase tracking-[0.25em] text-text-muted">Bred Slots</div>
						<div class="mt-1 text-xl font-black text-accent">{bredCount}</div>
					</div>
					<div class="rounded-lg border border-border bg-surface-alt p-2.5">
						<div class="text-[11px] uppercase tracking-[0.25em] text-text-muted">Parents Used</div>
						<div class="mt-1 text-xl font-black text-accent">{uniqueParents}</div>
					</div>
				</div>
				<div class="text-xs text-text-muted mt-auto">
					Mutated: <span class="font-semibold text-accent">{mutatedCount}</span>
					<span class="mx-1 text-text-muted">·</span>
					Helix = all slots; table = preserved only
				</div>
			</div>
		</div>

		{#if championEvents.length > 0}
			<div class="mt-3">
				<p class="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-text-muted">Preserved champions / elites</p>
				<div class="overflow-hidden rounded-lg border border-border bg-surface-alt">
					<div class="grid grid-cols-[50px_80px_minmax(0,1fr)_90px_90px] gap-0 border-b border-border bg-surface px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.22em] text-text-muted">
						<div>Slot</div>
						<div>Operator</div>
						<div>Parents</div>
						<div class="text-right">Mut. Rate</div>
						<div class="text-right">Mut. Strength</div>
					</div>
					{#each championEvents as event (event.slot)}
						{@const theme = operatorTheme(event.operator)}
						<div class={`grid grid-cols-[50px_80px_minmax(0,1fr)_90px_90px] items-center gap-0 border-t border-border px-3 py-1.5 text-xs text-text-primary ${theme.row}`}>
							<div class="flex items-center gap-1.5">
								<span class={`h-2 w-2 rounded-full ${theme.dot}`}></span>
								<span class="font-bold">#{event.slot}</span>
							</div>
							<div>
								<span class={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold ${theme.badge}`}>
									{prettyLabel(event.operator)}
								</span>
							</div>
							<div class="min-w-0 truncate text-text-muted font-mono text-[11px]">
								{#if event.parent_slots?.length > 0}
									{event.parent_slots.map(s => `#${s}`).join(' + ')}
								{:else}
									—
								{/if}
							</div>
							<div class="text-right font-mono text-[11px]">
								{event.mutation_rate != null ? (event.mutation_rate * 100).toFixed(1) + '%' : '—'}
							</div>
							<div class="text-right font-mono text-[11px]">
								{event.mutation_strength != null ? event.mutation_strength.toFixed(3) : '—'}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	{:else}
		<div class="rounded-2xl border border-dashed border-border bg-surface-alt px-5 py-10 text-center">
			<p class="text-base font-heading font-semibold text-text-primary">Breeding visualization will appear during training</p>
			<p class="mt-2 text-sm text-text-muted">
				Start a training session to see the genetic flow canvas and preserved-slot table.
			</p>
		</div>
	{/if}
</div>
