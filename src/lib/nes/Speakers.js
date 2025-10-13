/**
 * Speakers - Handles audio output with buffering
 * Based on jsnes-react implementation
 */

export class Speakers {
	/**
	 * Creates Speakers instance
	 * @param {Object} options - Configuration options
	 * @param {Function} [options.onBufferUnderrun] - Called when audio buffer is too low
	 */
	constructor({ onBufferUnderrun } = { onBufferUnderrun: undefined }) {
		this.onBufferUnderrun = onBufferUnderrun;
		
		// Audio context and node
		this.audioContext = null;
		this.scriptNode = null;
		
		// Circular buffer for audio samples
		this.bufferSize = 8192;
		/** @type {number[]} */
		this.buffer = [];
		this.writeIndex = 0;
		this.readIndex = 0;
		
		console.log('🔊 Speakers created');
	}

	/**
	 * Get the sample rate of the audio context
	 * @returns {number} Sample rate in Hz
	 */
	getSampleRate() {
		if (!window.AudioContext) {
			return 44100;
		}
		const tempCtx = new window.AudioContext();
		const sampleRate = tempCtx.sampleRate;
		tempCtx.close();
		return sampleRate;
	}

	/**
	 * Start audio playback
	 */
	start() {
		// Audio not supported
		if (!window.AudioContext) {
			console.warn('⚠️ AudioContext not supported');
			return;
		}

		try {
			// Only create audio context once
			if (!this.audioContext) {
				console.log('🔊 Creating new audio context');
				this.audioContext = new window.AudioContext();
				this.scriptNode = this.audioContext.createScriptProcessor(1024, 0, 2);
				this.scriptNode.onaudioprocess = this.onAudioProcess.bind(this);
				this.scriptNode.connect(this.audioContext.destination);
			}

			// Resume if suspended (requires user gesture)
			if (this.audioContext.state === 'suspended') {
				this.audioContext.resume().then(() => {
					console.log('✅ Audio context resumed');
				});
			}

			console.log('✅ Speakers started');
		} catch (error) {
			console.error('❌ Failed to start speakers:', error);
		}
	}

	/**
	 * Stop audio playback (pauses audio but keeps context alive for reuse)
	 */
	stop() {
		// Suspend audio context but don't close it (can be resumed later)
		if (this.audioContext && this.audioContext.state === 'running') {
			this.audioContext.suspend().then(() => {
				console.log('🔇 Audio context suspended');
			});
		}

		// Clear buffer
		this.readIndex = 0;
		this.writeIndex = 0;
		this.buffer = [];

		console.log('🔇 Speakers stopped');
	}

	/**
	 * Destroy speakers and clean up audio context (called on destroy)
	 */
	destroy() {
		if (this.scriptNode && this.audioContext) {
			this.scriptNode.disconnect();
			this.scriptNode.onaudioprocess = null;
			this.scriptNode = null;
		}

		if (this.audioContext) {
			this.audioContext.close().catch((error) => {
				console.warn('⚠️ Error closing audio context:', error);
			});
			this.audioContext = null;
		}

		console.log('🗑️ Speakers destroyed');
	}

	/**
	 * Write a sample pair to the buffer
	 * @param {number} left - Left channel sample
	 * @param {number} right - Right channel sample
	 */
	writeSample(left, right) {
		// Check for buffer overflow
		const currentSize = this.getBufferSize();
		if (currentSize >= this.bufferSize * 2) {
			// Buffer overflow - drop oldest samples
			console.warn('⚠️ Audio buffer overflow, dropping samples');
			this.readIndex = (this.readIndex + this.bufferSize) % (this.bufferSize * 2);
		}
		
		// Write samples
		this.buffer[this.writeIndex] = left;
		this.buffer[this.writeIndex + 1] = right;
		this.writeIndex = (this.writeIndex + 2) % (this.bufferSize * 2);
	}

	/**
	 * Get current buffer size (number of samples available)
	 * @returns {number} Number of samples in buffer
	 */
	getBufferSize() {
		if (this.writeIndex >= this.readIndex) {
			return this.writeIndex - this.readIndex;
		} else {
			return (this.bufferSize * 2) - this.readIndex + this.writeIndex;
		}
	}

	/**
	 * Audio process callback
	 * @param {AudioProcessingEvent} event - Audio processing event
	 */
	onAudioProcess(event) {
		const leftChannel = event.outputBuffer.getChannelData(0);
		const rightChannel = event.outputBuffer.getChannelData(1);
		const size = leftChannel.length;
		
		const bufferSize = this.getBufferSize() / 2; // Divide by 2 for sample pairs
		
		// Check for buffer underrun
		if (bufferSize < size && this.onBufferUnderrun) {
			this.onBufferUnderrun(bufferSize, size);
		}
		
		// Read samples from buffer
		for (let i = 0; i < size; i++) {
			if (this.getBufferSize() >= 2) {
				// Read sample pair
				leftChannel[i] = this.buffer[this.readIndex];
				rightChannel[i] = this.buffer[this.readIndex + 1];
				this.readIndex = (this.readIndex + 2) % (this.bufferSize * 2);
			} else {
				// Buffer underrun - output silence
				leftChannel[i] = 0;
				rightChannel[i] = 0;
			}
		}
	}
}

