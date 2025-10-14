"""
Simple Line Plot - Sine Wave Visualization

Demonstrates basic matplotlib line plotting with numpy.
Shows a sine wave with customized styling.
"""
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

