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
					badge: 'bg-amber-400/15 text-amber-200 border-amber-300/30',
					row: 'bg-amber-400/6',
					dot: 'bg-amber-300'
				};
			case 'sbx':
				return {
					badge: 'bg-cyan-400/15 text-cyan-200 border-cyan-300/30',
					row: 'bg-cyan-400/6',
					dot: 'bg-cyan-300'
				};
			case 'uniform':
				return {
					badge: 'bg-fuchsia-400/15 text-fuchsia-200 border-fuchsia-300/30',
					row: 'bg-fuchsia-400/6',
					dot: 'bg-fuchsia-300'
				};
			default:
				return {
					badge: 'bg-emerald-400/15 text-emerald-200 border-emerald-300/30',
					row: 'bg-emerald-400/6',
					dot: 'bg-emerald-300'
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
		<div class="mb-3 grid grid-cols-2 gap-2 md:grid-cols-4">
			<div class="rounded-xl border border-border bg-surface-alt p-2.5">
				<div class="text-[11px] uppercase tracking-[0.25em] text-text-muted">Events</div>
				<div class="mt-1 text-xl font-black text-text-primary">{events.length}</div>
			</div>
			<div class="rounded-xl border border-border bg-surface-alt p-2.5">
				<div class="text-[11px] uppercase tracking-[0.25em] text-text-muted">Preserved</div>
				<div class="mt-1 text-xl font-black text-accent">{preservedCount}</div>
			</div>
			<div class="rounded-xl border border-border bg-surface-alt p-2.5">
				<div class="text-[11px] uppercase tracking-[0.25em] text-text-muted">Bred Slots</div>
				<div class="mt-1 text-xl font-black text-accent">{bredCount}</div>
			</div>
			<div class="rounded-xl border border-border bg-surface-alt p-2.5">
				<div class="text-[11px] uppercase tracking-[0.25em] text-text-muted">Parents Used</div>
				<div class="mt-1 text-xl font-black text-accent">{uniqueParents}</div>
			</div>
		</div>

		<div class="mb-3">
			<BreedingGenArt breedingData={breedingData} />
		</div>

		<div class="mb-3 rounded-xl border border-border bg-callout px-3 py-2.5 text-[11px] leading-relaxed text-text-primary">
			<p class="font-semibold text-accent">How to read the helix</p>
			<ul class="mt-1.5 list-disc space-y-1 pl-4">
				<li>
					Each <strong>step along the helix</strong> is one population slot (one end = low slot index).
					Dot/rung color = how that slot was made:
					<span class="whitespace-nowrap text-amber-600">Champion</span>
					<span class="mx-1 text-text-muted">·</span>
					<span class="whitespace-nowrap text-sky-600">SBX</span>
					<span class="mx-1 text-text-muted">·</span>
					<span class="whitespace-nowrap text-fuchsia-600">Uniform</span>
					<span class="mx-1 text-text-muted">·</span>
					<span class="whitespace-nowrap text-emerald-600">Mutation</span>
				</li>
			</ul>
		</div>

		{#if championEvents.length > 0}
			<p class="mb-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-text-muted">Preserved champions / elites</p>
			<div class="overflow-hidden rounded-2xl border border-border bg-surface-alt">
				<div class="grid grid-cols-[72px_minmax(0,1fr)_110px] gap-0 border-b border-border bg-surface px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-text-muted">
					<div>Slot</div>
					<div>Lineage</div>
					<div>Operator</div>
				</div>
				{#each championEvents as event (event.slot)}
					{@const theme = operatorTheme(event.operator)}
					<div class={`grid grid-cols-[72px_minmax(0,1fr)_110px] items-center gap-0 border-t border-border px-3 py-2 text-xs text-text-primary ${theme.row}`}>
						<div class="flex items-center gap-2">
							<span class={`h-2 w-2 rounded-full ${theme.dot}`}></span>
							<span class="font-black text-text-primary">#{event.slot}</span>
						</div>
						<div class="min-w-0 truncate font-semibold text-accent">
							Champion from #{event.parent_slots[0] ?? '—'}
						</div>
						<div>
							<span class={`inline-flex rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${theme.badge}`}>
								{prettyLabel(event.operator)}
							</span>
						</div>
					</div>
				{/each}
			</div>
		{/if}

		<div class="mt-3 text-xs text-text-muted">
			Mutated children: <span class="font-semibold text-accent">{mutatedCount}</span>
			<span class="mx-2 text-text-muted">·</span>
			Helix = all slots; table = preserved only
		</div>
	{:else}
		<div class="rounded-2xl border border-dashed border-border bg-surface-alt px-5 py-10 text-center">
			<p class="text-base font-heading font-semibold text-text-primary">Breeding visualization will appear during training</p>
			<p class="mt-2 text-sm text-text-muted">
				Start a training session to see the genetic flow canvas and preserved-slot table.
			</p>
		</div>
	{/if}
</div>
