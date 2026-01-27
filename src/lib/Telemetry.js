/**
 * Telemetry Module for Mario AI Training
 *
 * Collects debug events during training cycles and dumps them at the end
 * for easier comparison between HeadlessNES and VisualNES behavior.
 */

class Telemetry {
	constructor() {
		this.events = [];
		this.enabled = true;
		this.cycleCount = 0;
		this.currentPhase = 'idle'; // 'idle', 'foreground', 'background'

		// Summary stats per cycle
		this.cycleSummary = {
			headless: { frames: [], resets: 0 },
			visual: { frames: [], resets: 0 },
			agent: { decisions: 0 },
			trainer: { generations: 0, bestDistance: 0, bestFitness: 0 }
		};
	}

	/**
	 * Enable/disable telemetry collection
	 */
	setEnabled(enabled) {
		this.enabled = enabled;
	}

	/**
	 * Set current phase
	 */
	setPhase(phase) {
		this.currentPhase = phase;
		this.log('system', `Phase changed to: ${phase}`);
	}

	/**
	 * Deep clone data to avoid Pyodide proxy issues
	 * When Python passes a dict to JS, it creates a borrowed proxy that gets
	 * destroyed when the Python function returns. We must clone immediately.
	 */
	_cloneData(data) {
		if (data === null || data === undefined) return null;
		try {
			// JSON round-trip ensures we get plain JS objects, not proxies
			return JSON.parse(JSON.stringify(data));
		} catch (e) {
			// If it can't be serialized, try to extract primitive values
			if (typeof data === 'object') {
				const clone = {};
				for (const key in data) {
					try {
						clone[key] = data[key];
					} catch (e2) {
						clone[key] = '[unserializable]';
					}
				}
				return clone;
			}
			return String(data);
		}
	}

	/**
	 * Log an event
	 * @param {string} category - 'headless', 'visual', 'agent', 'trainer', 'system'
	 * @param {string} message - Short description
	 * @param {object} data - Additional data (optional)
	 */
	log(category, message, data = null) {
		if (!this.enabled) return;

		// CRITICAL: Clone data immediately to avoid Pyodide proxy destruction
		const clonedData = this._cloneData(data);

		this.events.push({
			ts: performance.now(),
			phase: this.currentPhase,
			category,
			message,
			data: clonedData
		});

		// Update summary stats
		this._updateSummary(category, message, clonedData);
	}

	/**
	 * Log a frame state (for HeadlessNES/VisualNES comparison)
	 */
	logFrame(category, frameNum, state) {
		if (!this.enabled) return;

		// CRITICAL: For Pyodide dict proxies, use .get() method, not property access!
		// state.x returns undefined for Python dicts, but state.get('x') works
		const getValue = (key) => {
			try {
				// Try .get() for Python dict proxy
				if (typeof state.get === 'function') {
					return state.get(key);
				}
				// Fall back to property access for JS objects
				return state[key];
			} catch (e) {
				return 0;
			}
		};

		let buttons = [];
		try {
			const btnVal = getValue('buttons');
			buttons = btnVal ? Array.from(btnVal) : [];
		} catch (e) {
			buttons = [];
		}

		const frameData = {
			frame: frameNum,
			x: Number(getValue('x')) || 0,
			yOff: Number(getValue('yOff')) || 0,
			xOff: Number(getValue('xOff')) || 0,
			row: Number(getValue('row')) || 0,
			col: Number(getValue('col')) || 0,
			solids: Number(getValue('solids')) || 0,
			buttons: buttons
		};

		this.events.push({
			ts: performance.now(),
			phase: this.currentPhase,
			category,
			message: `Frame ${frameNum}`,
			data: frameData
		});

		// Track key frames for summary
		if ([0, 1, 2, 3, 4, 60, 120, 180].includes(frameNum)) {
			if (category === 'headless') {
				this.cycleSummary.headless.frames.push(frameData);
			} else if (category === 'visual') {
				this.cycleSummary.visual.frames.push(frameData);
			}
		}
	}

	/**
	 * Log a reset event
	 */
	logReset(category, afterFromJSON, afterSettle) {
		if (!this.enabled) return;

		// Clone data to avoid proxy issues
		const clonedData = {
			afterFromJSON: this._cloneData(afterFromJSON),
			afterSettle: this._cloneData(afterSettle)
		};

		this.events.push({
			ts: performance.now(),
			phase: this.currentPhase,
			category,
			message: 'Reset',
			data: clonedData
		});

		if (category === 'headless') {
			this.cycleSummary.headless.resets++;
		} else if (category === 'visual') {
			this.cycleSummary.visual.resets++;
		}
	}

	/**
	 * Update summary stats
	 */
	_updateSummary(category, message, data) {
		if (category === 'trainer' && data) {
			if (data.generation !== undefined) {
				this.cycleSummary.trainer.generations = data.generation;
			}
			if (data.bestDistance !== undefined) {
				this.cycleSummary.trainer.bestDistance = data.bestDistance;
			}
			if (data.bestFitness !== undefined) {
				this.cycleSummary.trainer.bestFitness = data.bestFitness;
			}
		}
		if (category === 'agent') {
			this.cycleSummary.agent.decisions++;
		}
	}

	/**
	 * Dump all collected telemetry and clear
	 */
	dump(label = null) {
		if (!this.enabled || this.events.length === 0) return;

		this.cycleCount++;
		const cycleLabel = label || `Cycle ${this.cycleCount}`;

		console.group(`%c[Telemetry] ${cycleLabel}`, 'color: #9b59b6; font-weight: bold');

		// Summary
		console.group('%cSummary', 'color: #3498db; font-weight: bold');
		console.log(`Trainer: Gen ${this.cycleSummary.trainer.generations}, Best Distance: ${this.cycleSummary.trainer.bestDistance}, Best Fitness: ${this.cycleSummary.trainer.bestFitness}`);
		console.log(`HeadlessNES Resets: ${this.cycleSummary.headless.resets}`);
		console.log(`VisualNES Resets: ${this.cycleSummary.visual.resets}`);
		console.log(`Agent Decisions: ${this.cycleSummary.agent.decisions}`);
		console.groupEnd();

		// Frame comparison
		this._dumpFrameComparison();

		// All events (collapsed)
		console.groupCollapsed('%cAll Events (' + this.events.length + ')', 'color: #7f8c8d');
		for (const event of this.events) {
			const timeStr = (event.ts / 1000).toFixed(3);
			const dataStr = event.data ? JSON.stringify(event.data) : '';
			console.log(`[${timeStr}s] [${event.phase}] [${event.category}] ${event.message}`, dataStr ? event.data : '');
		}
		console.groupEnd();

		console.groupEnd();

		this.clear();
	}

	/**
	 * Dump frame comparison between HeadlessNES and VisualNES
	 */
	_dumpFrameComparison() {
		const headless = this.cycleSummary.headless.frames;
		const visual = this.cycleSummary.visual.frames;

		if (headless.length === 0 && visual.length === 0) return;

		console.group('%cFrame Comparison (HeadlessNES vs VisualNES)', 'color: #e74c3c; font-weight: bold');

		// Build comparison table
		const allFrameNums = new Set([
			...headless.map(f => f.frame),
			...visual.map(f => f.frame)
		]);

		const rows = [];
		for (const frameNum of [...allFrameNums].sort((a, b) => a - b)) {
			const h = headless.find(f => f.frame === frameNum);
			const v = visual.find(f => f.frame === frameNum);

			const row = {
				frame: frameNum,
				'H.x': h?.x ?? '-',
				'V.x': v?.x ?? '-',
				'H.yOff': h?.yOff ?? '-',
				'V.yOff': v?.yOff ?? '-',
				'H.row': h?.row ?? '-',
				'V.row': v?.row ?? '-',
				'match': h && v ? (h.x === v.x && h.yOff === v.yOff ? '✓' : '✗') : '?'
			};
			rows.push(row);
		}

		if (rows.length > 0) {
			console.table(rows);

			// Highlight mismatches
			const mismatches = rows.filter(r => r.match === '✗');
			if (mismatches.length > 0) {
				console.warn(`%c${mismatches.length} frame mismatches detected!`, 'color: #e74c3c; font-weight: bold');
			} else if (rows.every(r => r.match === '✓')) {
				console.log('%cAll frames match!', 'color: #27ae60; font-weight: bold');
			}
		}

		console.groupEnd();
	}

	/**
	 * Clear all events and reset summary
	 */
	clear() {
		this.events = [];
		this.cycleSummary = {
			headless: { frames: [], resets: 0 },
			visual: { frames: [], resets: 0 },
			agent: { decisions: 0 },
			trainer: { generations: 0, bestDistance: 0, bestFitness: 0 }
		};
	}

	/**
	 * Get events for a specific category
	 */
	getEvents(category = null) {
		if (!category) return this.events;
		return this.events.filter(e => e.category === category);
	}

	/**
	 * Get current summary
	 */
	getSummary() {
		return { ...this.cycleSummary };
	}
}

// Singleton instance
const telemetry = new Telemetry();

// Expose on window for Python access
if (typeof window !== 'undefined') {
	window.telemetry = telemetry;

	// Convenience methods for Python
	window.telemetryLog = (category, message, data) => telemetry.log(category, message, data);
	window.telemetryLogFrame = (category, frameNum, state) => telemetry.logFrame(category, frameNum, state);
	window.telemetrySetPhase = (phase) => telemetry.setPhase(phase);
	window.telemetryDump = (label) => telemetry.dump(label);
	window.telemetryClear = () => telemetry.clear();
}

export { telemetry, Telemetry };
export default telemetry;
