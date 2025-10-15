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
    this.scrollToBottom = this.scrollToBottom.bind(this);
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
    this.window.setTimeout(() => {
      this.resizeTerminal();
      this.setupAutoscroll();
    }, 100);
    this.window.term = document.getElementById("console-script")?.terminal;
  }

  /**
   * Resizes the PyScript terminal after the dialog becomes visible.
   * @returns {void}
   */
  resizeTerminal() {
    const term = document.getElementById("console-script")?.terminal;
    const container = document.getElementById("console-content");
  
    if (!term || !container) {
      console.warn("Terminal or container not found");
      return;
    }
    
    const width = container.clientWidth;
    const height = container.clientHeight;
  
    term.resize(width, height); // call resize with pixel dimensions
    console.log(`Terminal resized to ${width}x${height} pixels`);
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
    const term = document.getElementById("console-script").terminal;
    if (!term) {
      console.warn('Terminal not found');
      return;
    }
    term.clear();
  }

  /**
   * Copies the console content to clipboard when the copy button is clicked.
   * @returns {void}
   */
  async handleCopyClick() {
    term.selectAll();
    const selection = term.getSelection();
    await navigator.clipboard.writeText(selection);
    term.clearSelection();
  }

  /**
   * Opens the console dialog when the footer button is clicked.
   * @returns {void}
   */
  handleOpenClick() {
    this.openConsole();
  }

  /**
   * Scrolls the terminal viewport to the bottom.
   * @returns {void}
   */
  scrollToBottom() {
    const terminal = this.document.querySelector('#console-content py-terminal');
    if (terminal) {
      const viewport = terminal.querySelector('.xterm-viewport');
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }

  /**
   * Sets up autoscroll by hooking into xterm's write events.
   * @returns {void}
   */
  setupAutoscroll() {
    const term = this.document.getElementById("console-script")?.terminal;

    if (!term) {
      // Try again after a delay if terminal not ready yet
      setTimeout(() => this.setupAutoscroll(), 500);
      return;
    }

    // Hook into xterm's onWriteParsed event (fires after content is written)
    term.onWriteParsed(() => {
      this.scrollToBottom();
    });

    // Initial scroll to bottom
    this.scrollToBottom();
  }
}
