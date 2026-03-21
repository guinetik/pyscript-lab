/**
 * DNA-inspired lineage viz: a genuinely rotating 3D-projected particle helix.
 * The helix itself rotates in projection space, instead of rotating the whole
 * canvas plane with CSS.
 *
 * @module breedingGenArtCanvas
 */

/**
 * @typedef {Object} BreedingEvent
 * @property {number} slot
 * @property {string} mode
 * @property {string} operator
 * @property {number[]} parent_slots
 * @property {boolean} preserved
 * @property {boolean} mutated
 * @property {number} mutation_rate
 * @property {number} mutation_strength
 */

/**
 * @typedef {Object} BreedingData
 * @property {number} generation
 * @property {string} mode
 * @property {BreedingEvent[]} events
 */

/**
 * @param {string} operator
 * @returns {{ r: number, g: number, b: number }}
 */
export function operatorRgb(operator) {
	switch (operator) {
		case 'preserve':
			return { r: 250, g: 204, b: 21 };
		case 'sbx':
			return { r: 56, g: 189, b: 248 };
		case 'uniform':
			return { r: 217, g: 70, b: 239 };
		case 'mutation':
			return { r: 74, g: 222, b: 128 };
		default:
			return { r: 148, g: 163, b: 184 };
	}
}

/**
 * @param {HTMLCanvasElement} canvas
 * @returns {{ ctx: CanvasRenderingContext2D, cssW: number, cssH: number }}
 */
export function setupCanvas(canvas) {
	const dpr = typeof window !== 'undefined' ? Math.min(2, window.devicePixelRatio || 1) : 1;
	const rect = canvas.getBoundingClientRect();
	const bw = Math.max(1, Math.floor(rect.width * dpr));
	const bh = Math.max(1, Math.floor(rect.height * dpr));
	if (canvas.width !== bw || canvas.height !== bh) {
		canvas.width = bw;
		canvas.height = bh;
	}
	const ctx = canvas.getContext('2d', { alpha: true });
	if (!ctx) {
		throw new Error('2d context unavailable');
	}
	ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
	return { ctx, cssW: rect.width, cssH: rect.height };
}

/**
 * Project a 3D helix point into 2D screen space using a rotating yaw.
 * @param {number} theta
 * @param {number} yNorm
 * @param {number} radius
 * @param {number} centerX
 * @param {number} topPad
 * @param {number} helixHeight
 * @param {number} yaw
 * @param {number} perspective
 * @param {number} cameraDistance
 * @returns {{ sx: number, sy: number, depth: number, scale: number }}
 */
function projectHelixPoint(theta, yNorm, radius, centerX, topPad, helixHeight, yaw, perspective, cameraDistance) {
	const xw = radius * Math.cos(theta);
	const zw = radius * Math.sin(theta);
	const xr = xw * Math.cos(yaw) + zw * Math.sin(yaw);
	const zr = -xw * Math.sin(yaw) + zw * Math.cos(yaw);
	const scale = perspective / (cameraDistance - zr);
	const yw = topPad + yNorm * helixHeight;
	return {
		sx: centerX + xr * scale,
		sy: yw + zr * 0.1,
		depth: zr,
		scale
	};
}

/**
 * Draw a rotating 3D particle double helix.
 *
 * @param {HTMLCanvasElement} canvas
 * @param {BreedingData | null} data
 * @param {number} rotationPhase - radians, applied as yaw to the helix
 */
export function drawBreedingHelix(canvas, data, rotationPhase = 0) {
	const { ctx, cssW: w, cssH: h } = setupCanvas(canvas);

	const padX = 12;
	const padTop = 36;
	const padBot = 26;
	const helixH = Math.max(50, h - padTop - padBot);
	const cx = w * 0.5;
	const R = Math.min(52, (w - 2 * padX) * 0.36);
	const turns = 2.4;
	const perspective = 220;
	const cameraDistance = 170;

	ctx.fillStyle = '#F3EDE4';
	ctx.fillRect(0, 0, w, h);

	if (!data?.events?.length) {
		ctx.fillStyle = '#2C2C2C';
		ctx.font = "600 13px 'Source Sans 3', sans-serif";
		ctx.textAlign = 'center';
		ctx.fillText('Particle helix appears when training runs', w / 2, h * 0.52);
		ctx.fillStyle = '#6B6560';
		ctx.font = "500 11px 'Source Sans 3', sans-serif";
		ctx.fillText('Dots = slots · helix rotates in true 3D projection', w / 2, h * 0.58);
		return;
	}

	const events = data.events;
	const n = events.length;

	ctx.fillStyle = '#2C2C2C';
	ctx.font = "700 10px 'Source Sans 3', sans-serif";
	ctx.textAlign = 'left';
	ctx.fillText(`Gen ${data.generation} · ${data.mode}`, padX, 16);
	ctx.textAlign = 'right';
	ctx.fillStyle = '#6B6560';
	ctx.font = "600 9px 'Source Sans 3', sans-serif";
	ctx.fillText('3D helix rotation · color = operator', w - padX, 16);

	/** @type {{ sx: number, sy: number, depth: number, r: number, g: number, b: number, a: number, rad: number }[]} */
	const particles = [];

	for (let i = 0; i < n; i++) {
		const u = n <= 1 ? 0.5 : i / (n - 1);
		const ev = events[i];
		const { r, g, b } = operatorRgb(ev.operator);
		const thetaL = u * turns * Math.PI * 2 + rotationPhase;
		const thetaR = thetaL + Math.PI;

		const pL = projectHelixPoint(thetaL, u, R, cx, padTop, helixH, 0, perspective, cameraDistance);
		const pR = projectHelixPoint(thetaR, u, R, cx, padTop, helixH, 0, perspective, cameraDistance);

		const depthNormL = (pL.depth / R + 1) * 0.5;
		const depthNormR = (pR.depth / R + 1) * 0.5;
		const baseA = ev.preserved ? 0.94 : 0.32;
		const radL = (ev.preserved ? 3.4 : 2.0) * pL.scale;
		const radR = (ev.preserved ? 3.0 : 1.8) * pR.scale;

		particles.push({ sx: pL.sx, sy: pL.sy, depth: pL.depth, r, g, b, a: baseA * (0.55 + depthNormL * 0.45), rad: radL });
		particles.push({ sx: pR.sx, sy: pR.sy, depth: pR.depth, r, g, b, a: baseA * (0.5 + depthNormR * 0.45), rad: radR });

		// Faint rung to keep the DNA read clear without looking like a graph.
		if (i % (n > 90 ? 2 : 1) === 0) {
			const midDepth = (pL.depth + pR.depth) * 0.5;
			const dn = (midDepth / R + 1) * 0.5;
			ctx.strokeStyle = `rgba(${r},${g},${b},${0.08 + dn * 0.12})`;
			ctx.lineWidth = 0.9 * ((pL.scale + pR.scale) * 0.5);
			ctx.beginPath();
			ctx.moveTo(pL.sx, pL.sy);
			ctx.lineTo(pR.sx, pR.sy);
			ctx.stroke();
		}
	}

	particles.sort((a, b) => a.depth - b.depth);

	for (const p of particles) {
		ctx.beginPath();
		ctx.fillStyle = `rgba(${p.r},${p.g},${p.b},${p.a})`;
		ctx.arc(p.sx, p.sy, p.rad, 0, Math.PI * 2);
		ctx.fill();
	}

	ctx.textAlign = 'center';
	ctx.fillStyle = '#6B6560';
	ctx.font = "600 8px 'Source Sans 3', sans-serif";
	ctx.fillText(`${n} loci · rotating 3D projection`, cx, h - 8);
}

/** @deprecated */
export const drawBreedingGenArt = drawBreedingHelix;
