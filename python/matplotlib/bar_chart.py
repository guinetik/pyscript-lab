"""
Bar Chart - Programming Language Popularity

Demonstrates categorical data visualization with colored bars
and value labels.
"""
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

