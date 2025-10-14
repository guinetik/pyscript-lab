"""
Scatter Plot - Data Correlation Visualization

Demonstrates scatter plot with color mapping using viridis colormap.
Shows correlation between x and y values with added noise.
"""
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

