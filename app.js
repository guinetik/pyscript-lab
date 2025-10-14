/**
 * Controller responsible for initializing PyScript L.A.B application behaviors.
 */
export default class App {
  /**
   * Creates a new application controller instance.
   * @param {Document} doc - The document object to operate on.
   * @param {Window} win - The window object providing global APIs.
   */
  constructor(doc = document, win = window) {
    this.document = doc;
    this.window = win;

    this.loading = this.document.getElementById('loading');
    this.consoleDialog = null;
    this.titleBar = null;
    this.closeBtn = null;
    this.clearBtn = null;
    this.copyBtn = null;
    this.openBtn = null;

    this.isDragging = false;
    this.currentX = 0;
    this.currentY = 0;
    this.initialX = 0;
    this.initialY = 0;
    this.xOffset = 0;
    this.yOffset = 0;
    this.consoleInitialized = false;

    this.handlePyAllDone = this.handlePyAllDone.bind(this);
    this.openConsole = this.openConsole.bind(this);
    this.resizeTerminal = this.resizeTerminal.bind(this);
    this.initializeConsole = this.initializeConsole.bind(this);
    this.dragStart = this.dragStart.bind(this);
    this.drag = this.drag.bind(this);
    this.dragEnd = this.dragEnd.bind(this);
    this.handleCloseClick = this.handleCloseClick.bind(this);
    this.handleClearClick = this.handleClearClick.bind(this);
    this.handleCopyClick = this.handleCopyClick.bind(this);
    this.handleOpenClick = this.handleOpenClick.bind(this);
  }

  /**
   * Initializes the application by wiring up global behaviors and event listeners.
   * @returns {void}
   */
  init() {
    if (this.loading) {
      this.window.addEventListener('py:all-done', this.handlePyAllDone);
      this.loading.showModal();
      this.loading.innerHTML = '<h1>Loading PyScript Runtime...</h1>';
    }

    if (typeof this.window.Bokeh !== 'undefined') {
      this.window.Bokeh.set_log_level('info');
    }

    this.window.openConsole = this.openConsole;

    if (this.document.readyState === 'loading') {
      this.document.addEventListener('DOMContentLoaded', this.initializeConsole);
    } else {
      this.initializeConsole();
    }
  }

  /**
   * Handles the PyScript initialization completion event by closing the loading dialog.
   * @returns {void}
   */
  handlePyAllDone() {
    if (this.loading) {
      this.loading.close();
    }
  }

  /**
   * Opens the console dialog and ensures the embedded terminal resizes to fit its container.
   * @returns {void}
   */
  openConsole() {
    if (!this.consoleDialog) {
      this.consoleDialog = this.document.getElementById('console');
    }

    if (!this.consoleDialog) {
      return;
    }

    this.consoleDialog.showModal();
    this.window.setTimeout(this.resizeTerminal, 100);
  }

  /**
   * Resizes the PyScript terminal after the dialog becomes visible.
   * @returns {void}
   */
  resizeTerminal() {
    if (!this.consoleDialog) {
      return;
    }

    const terminal = this.consoleDialog.querySelector('py-terminal');
    if (terminal && terminal._terminal && terminal._terminal.fit) {
      terminal._terminal.fit.fit();
    }
  }

  /**
   * Initializes console drag, clear, and open interactions once the DOM content is loaded.
   * @returns {void}
   */
  initializeConsole() {
    if (this.consoleInitialized) {
      return;
    }

    this.consoleDialog = this.document.getElementById('console');
    this.titleBar = this.document.querySelector('.console-title-bar');
    this.closeBtn = this.document.querySelector('.console-close');
    this.clearBtn = this.document.getElementById('console-clear-btn');
    this.copyBtn = this.document.getElementById('console-copy-btn');
    this.openBtn = this.document.getElementById('open-console-btn');

    if (!this.consoleDialog || !this.titleBar || !this.closeBtn || !this.clearBtn || !this.copyBtn || !this.openBtn) {
      return;
    }

    this.titleBar.addEventListener('mousedown', this.dragStart);
    this.document.addEventListener('mousemove', this.drag);
    this.document.addEventListener('mouseup', this.dragEnd);
    this.closeBtn.addEventListener('click', this.handleCloseClick);
    this.clearBtn.addEventListener('click', this.handleClearClick);
    this.copyBtn.addEventListener('click', this.handleCopyClick);
    this.openBtn.addEventListener('click', this.handleOpenClick);

    this.consoleInitialized = true;
  }

  /**
   * Begins the drag behavior for the console dialog when the title bar is pressed.
   * @param {MouseEvent} event - Mouse event carrying the pointer position.
   * @returns {void}
   */
  dragStart(event) {
    this.initialX = event.clientX - this.xOffset;
    this.initialY = event.clientY - this.yOffset;
    if (event.target === this.titleBar) {
      this.isDragging = true;
    }
  }

  /**
   * Updates the console dialog position while dragging.
   * @param {MouseEvent} event - Mouse event that provides the current pointer position.
   * @returns {void}
   */
  drag(event) {
    if (!this.isDragging || !this.consoleDialog) {
      return;
    }

    event.preventDefault();
    this.currentX = event.clientX - this.initialX;
    this.currentY = event.clientY - this.initialY;
    this.xOffset = this.currentX;
    this.yOffset = this.currentY;
    this.consoleDialog.style.transform = `translate(${this.currentX}px, ${this.currentY}px)`;
  }

  /**
   * Ends the drag interaction for the console dialog.
   * @returns {void}
   */
  dragEnd() {
    this.isDragging = false;
  }

  /**
   * Handles the close button click event for the console dialog.
   * @returns {void}
   */
  handleCloseClick() {
    if (this.consoleDialog) {
      this.consoleDialog.close();
    }
  }

  /**
   * Clears the console output area when the clear button is clicked.
   * @returns {void}
   */
  handleClearClick() {
    const consoleScript = this.document.getElementById('console-script');
    if (consoleScript && consoleScript._internal && consoleScript._internal.clear) {
      consoleScript._internal.clear();
      return;
    }

    const outputs = this.document.querySelectorAll('#console-content py-terminal');
    outputs.forEach(output => {
      if (typeof output.clear === 'function') {
        output.clear();
      }
    });

    const consoleOut = this.document.querySelector('#console-content');
    const pyScript = consoleOut ? consoleOut.querySelector('script[type="py"]') : null;
    if (consoleOut && pyScript) {
      consoleOut.innerHTML = '';
      consoleOut.appendChild(pyScript);
    }
  }

  /**
   * Copies the console content to clipboard when the copy button is clicked.
   * @returns {void}
   */
  handleCopyClick() {
    const terminal = this.document.querySelector('#console-content py-terminal');

    if (!terminal) {
      console.warn('Terminal not found');
      return;
    }

    // Try to get terminal buffer content
    let text = '';

    // Method 1: Try xterm.js buffer API
    if (terminal._terminal && terminal._terminal.buffer) {
      const buffer = terminal._terminal.buffer.active;
      const lines = [];

      for (let i = 0; i < buffer.length; i++) {
        const line = buffer.getLine(i);
        if (line) {
          lines.push(line.translateToString(true));
        }
      }

      text = lines.join('\n');
    }

    // Method 2: Fallback to visible text content
    if (!text) {
      const xtermScreen = terminal.querySelector('.xterm-screen');
      if (xtermScreen) {
        text = xtermScreen.textContent || '';
      }
    }

    // Copy to clipboard
    if (text) {
      navigator.clipboard.writeText(text).then(() => {
        // Show feedback
        if (this.copyBtn) {
          const originalText = this.copyBtn.innerHTML;
          this.copyBtn.innerHTML = '✓ Copied!';
          setTimeout(() => {
            this.copyBtn.innerHTML = originalText;
          }, 2000);
        }
      }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
      });
    } else {
      console.warn('No content to copy');
    }
  }

  /**
   * Opens the console dialog when the footer button is clicked.
   * @returns {void}
   */
  handleOpenClick() {
    this.openConsole();
  }
}
