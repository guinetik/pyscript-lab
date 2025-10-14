import"../chunks/Bzak7iHL.js";import"../chunks/CIFhvQNR.js";import{f as l,t as m,a as s,w as y,c as r,r as i,n as h}from"../chunks/DH-y7u4P.js";import{s as g}from"../chunks/BO_s36dd.js";import{p as u}from"../chunks/C7OzWLIK.js";import{E as b}from"../chunks/UjML23Vg.js";var v=y(l(`<section slot="py_slot" class="pyscript p-5"><h1>Example 1: Pyodide REPL</h1> <script type="py-editor" id="py-editor">
import sys
print(sys.version)
a = 42
print(a)
		<\/script> <hr class="my-4"/> <h1>Example 2: MicroPython REPL</h1> <script type="mpy-editor" id="mpy-editor" language="python">
import sys
print(sys.version)
a = 42
print(a)
		<\/script></section>`)),P=l(`<article slot="content_slot"><h2 class="mb-5 text-xl font-extrabold"> </h2> <div class="prose max-w-none"><p class="mb-4">PyScript's REPL (Read-Evaluate-Print-Loop) provides an interactive Python environment directly in your browser.
				Using either Pyodide or MicroPython interpreters, you can write, execute, and see results of Python code in real-time,
				similar to Jupyter notebooks but without any server infrastructure.</p> <div class="mb-6 rounded-lg bg-gray-100 p-4"><h3 class="mb-2 text-lg font-bold">What You Can Do:</h3> <ul class="list-disc space-y-2 pl-5"><li><strong>Interactive Coding:</strong> Write and execute Python code on the fly</li> <li><strong>Multiple Interpreters:</strong> Choose between Pyodide (full CPython) or MicroPython (lightweight)</li> <li><strong>Editable Code:</strong> Modify examples and see results instantly</li> <li><strong>Standard Library Access:</strong> Use Python's built-in modules like <code class="rounded bg-white px-1">sys</code>, <code class="rounded bg-white px-1">math</code>, and more</li></ul></div> <div class="mb-6 rounded-lg bg-blue-50 p-4"><h3 class="mb-2 text-lg font-bold">Implementation:</h3> <p class="mb-2">REPL editors are created using special script types:</p> <pre class="rounded bg-white p-3 text-sm overflow-x-auto"><code>&lt;script type="py-editor"&gt;
  # Your Python code here
  print("Hello from Pyodide!")
&lt;/script&gt;

&lt;script type="mpy-editor"&gt;
  # MicroPython version
  print("Hello from MicroPython!")
&lt;/script&gt;</code></pre></div> <div class="mb-4 rounded-lg bg-green-50 p-4"><h3 class="mb-2 text-lg font-bold">Use Cases:</h3> <ul class="list-disc space-y-2 pl-5"><li>Educational tutorials and code demonstrations</li> <li>Interactive documentation</li> <li>Prototyping Python algorithms</li> <li>Live coding environments</li></ul></div></div></article>`);function C(n,a){let p=u(a,"name",8,"REPL");b(n,{props:{previousPage:"/examples/basics/hello",nextPage:"/examples/basics/interop"},$$slots:{py_slot:(e,c)=>{var t=v();s(e,t)},content_slot:(e,c)=>{var t=P(),o=r(t),d=r(o,!0);i(o),h(2),i(t),m(()=>g(d,p())),s(e,t)}}})}export{C as component};
