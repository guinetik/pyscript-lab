<script>
	import ExperimentCard from '$lib/ExperimentCard.svelte';
	import PyExample from '$lib/PyExample.svelte';
	export let name = 'Matplotlib Introduction';
</script>

<ExperimentCard props={{ previousPage: '/examples/diagrams', nextPage: '/examples/matplotlib/charts' }}>
	<div slot="py_slot">
		<section class="pyscript p-5">
			<h1>Example 1: Simple Line Plot</h1>
			<PyExample title="A basic line chart with matplotlib:">
				<script type="py" id="matplotlib-line">
from pyscript import display
import matplotlib.pyplot as plt
import numpy as np

# Create sample data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Create the plot
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(x, y, linewidth=2, color='blue')
ax.set_title('Sine Wave', fontsize=16, fontweight='bold')
ax.set_xlabel('X axis', fontsize=12)
ax.set_ylabel('Y axis', fontsize=12)
ax.grid(True, alpha=0.3)

# Display the plot
display(fig, target="matplotlib-line-output")
				</script>
			</PyExample>
			<div id="matplotlib-line-output"></div>

			<hr class="my-4" />

			<h1>Example 2: Bar Chart</h1>
			<PyExample title="A colorful bar chart:">
				<script type="py" id="matplotlib-bar">
from pyscript import display
import matplotlib.pyplot as plt

# Sample data
categories = ['Python', 'JavaScript', 'Java', 'C++', 'Go']
values = [85, 72, 68, 55, 48]
colors = ['#3776ab', '#f7df1e', '#007396', '#00599c', '#00add8']

# Create bar chart
fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(categories, values, color=colors, alpha=0.8)
ax.set_title('Programming Language Popularity', fontsize=16, fontweight='bold')
ax.set_ylabel('Popularity Score', fontsize=12)
ax.set_ylim(0, 100)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

# Display the plot
display(fig, target="matplotlib-bar-output")
				</script>
			</PyExample>
			<div id="matplotlib-bar-output"></div>

			<hr class="my-4" />

			<h1>Example 3: Scatter Plot</h1>
			<PyExample title="Data correlation visualization:">
				<script type="py" id="matplotlib-scatter">
from pyscript import display
import matplotlib.pyplot as plt
import numpy as np

# Generate random data
np.random.seed(42)
x = np.random.randn(100)
y = 2 * x + np.random.randn(100) * 0.5

# Create scatter plot
fig, ax = plt.subplots(figsize=(8, 5))
scatter = ax.scatter(x, y, c=y, cmap='viridis', alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
ax.set_title('Scatter Plot with Correlation', fontsize=16, fontweight='bold')
ax.set_xlabel('X values', fontsize=12)
ax.set_ylabel('Y values', fontsize=12)
ax.grid(True, alpha=0.3)

# Add colorbar
plt.colorbar(scatter, ax=ax, label='Y value')

# Display the plot
display(fig, target="matplotlib-scatter-output")
				</script>
			</PyExample>
			<div id="matplotlib-scatter-output"></div>
		</section>
	</div>
	<article slot="content_slot">
		<h2 class="mb-5 text-xl font-extrabold">{name}</h2>

		<div class="prose max-w-none">
			<p class="mb-4">
				Matplotlib is Python's most popular plotting library, and with PyScript, you can run it
				directly in your browser! Create interactive visualizations, charts, and graphs without
				any server-side processing—all powered by WebAssembly and Pyodide.
			</p>

			<div class="mb-6 rounded-lg bg-gray-100 p-4">
				<h3 class="mb-2 text-lg font-bold">Key Features:</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li><strong>Full Matplotlib Support:</strong> Access the complete matplotlib API in the browser</li>
					<li><strong>NumPy Integration:</strong> Use NumPy arrays for data manipulation</li>
					<li><strong>Interactive Charts:</strong> Create line plots, bar charts, scatter plots, and more</li>
					<li><strong>Customization:</strong> Full control over colors, styles, labels, and layout</li>
					<li><strong>Zero Backend:</strong> All rendering happens client-side</li>
				</ul>
			</div>

			<div class="mb-6 rounded-lg bg-blue-50 p-4">
				<h3 class="mb-2 text-lg font-bold">The Examples:</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li><strong>Example 1:</strong> Line Plot - Shows a sine wave with customized styling</li>
					<li><strong>Example 2:</strong> Bar Chart - Demonstrates categorical data visualization</li>
					<li><strong>Example 3:</strong> Scatter Plot - Visualizes data correlation with color mapping</li>
				</ul>
			</div>

			<div class="mb-4 rounded-lg bg-green-50 p-4">
				<h3 class="mb-2 text-lg font-bold">Getting Started:</h3>
				<p class="mb-2">To use Matplotlib in PyScript, you need to specify it in your config:</p>
				<pre class="rounded bg-white p-3 text-sm overflow-x-auto"><code>&lt;py-config&gt;
  packages = ["matplotlib", "numpy"]
&lt;/py-config&gt;

&lt;script type="py"&gt;
  from pyscript import display
  import matplotlib.pyplot as plt
  # Create your plots
  fig, ax = plt.subplots()
  # ... customize your plot
  display(fig, target="output-div")
&lt;/script&gt;</code></pre>
				<p class="mt-3 text-sm">
					<strong>Note:</strong> Matplotlib plots are rendered as static images in PyScript. For interactive
					plots, consider using Bokeh (see Bokeh examples).
				</p>
			</div>

			<div class="mb-6 rounded-lg bg-yellow-50 p-4">
				<h3 class="mb-2 text-lg font-bold">Use Cases:</h3>
				<ul class="list-disc space-y-2 pl-5">
					<li>Data visualization dashboards</li>
					<li>Scientific and educational demonstrations</li>
					<li>Statistical analysis presentations</li>
					<li>Report generation with charts</li>
				</ul>
			</div>
		</div>
	</article>
</ExperimentCard>
