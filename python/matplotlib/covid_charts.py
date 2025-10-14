"""
COVID-19 Data Charts - Multi-Chart Analysis

Demonstrates advanced matplotlib usage with real-world pandemic data:
- Horizontal bar charts with heatmap styling
- Pie charts with region distribution
- Scatter plots with log scale
- Case fatality rate analysis

Data Source: covid_country.csv (187 countries/regions)

Author: PyScript Lab
"""
from pyscript import display
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pyodide.http import open_url
from matplotlib.patches import Patch
import asyncio


class CovidChartsVisualizer:
    """
    COVID-19 Data Visualization Suite
    
    Generates multiple chart types to analyze pandemic data from 187 countries.
    Each chart is rendered to a specific target element in the DOM.
    
    Attributes:
        df (pd.DataFrame): The loaded COVID-19 dataset
    """
    
    def __init__(self):
        """
        Initialize the visualizer by loading data and generating all charts.
        """
        self.df = None
        self.load_data()
    
    def load_data(self):
        """
        Load COVID-19 data from CSV file.
        
        Loads the dataset and prints summary statistics to console.
        """
        self.df = pd.read_csv(open_url('/data/covid_country.csv'))
        print(f"📊 Loaded data for {len(self.df)} countries/regions")
        print(f"Total Deaths: {self.df['Deaths'].sum():,}")
        print(f"Total Confirmed Cases: {self.df['Confirmed'].sum():,}")
    
    async def generate_top_deaths_chart(self):
        """
        Generate horizontal bar chart showing top 20 countries by deaths.
        
        Creates a heatmap-style visualization where color intensity
        increases with death count. Displays in 'covid-chart1' element.
        """
        await asyncio.sleep(0)  # Yield control to event loop
        top_deaths = self.df.nlargest(20, 'Deaths')[['Country/Region', 'Deaths']].sort_values('Deaths')
        
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(top_deaths)))
        bars = ax.barh(top_deaths['Country/Region'], top_deaths['Deaths'], color=colors)
        ax.set_xlabel('Total Deaths', fontsize=12, fontweight='bold')
        ax.set_title('Top 20 Countries by COVID-19 Deaths', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, (idx, row) in enumerate(top_deaths.iterrows()):
            ax.text(row['Deaths'], i, f" {int(row['Deaths']):,}",
                   va='center', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        display(fig, target="covid-chart1")
    
    async def generate_regional_deaths_pie(self):
        """
        Generate pie chart showing death distribution by WHO region.
        
        Groups deaths by WHO region and displays as a pie chart with
        percentages. Displays in 'covid-chart2' element.
        """
        await asyncio.sleep(0)  # Yield control to event loop
        region_deaths = self.df.groupby('WHO Region')['Deaths'].sum().sort_values(ascending=False)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set3(range(len(region_deaths)))
        wedges, texts, autotexts = ax.pie(
            region_deaths, 
            labels=region_deaths.index, 
            autopct='%1.1f%%',
            colors=colors, 
            startangle=90
        )
        ax.set_title('COVID-19 Deaths Distribution by WHO Region', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        plt.tight_layout()
        display(fig, target="covid-chart2")
    
    async def generate_cases_vs_deaths_scatter(self):
        """
        Generate scatter plot showing correlation between cases and deaths.
        
        Uses log scale for both axes to handle wide range of values.
        Color-coded by WHO region. Displays in 'covid-chart3' element.
        """
        await asyncio.sleep(0)  # Yield control to event loop
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Color by WHO Region
        regions = self.df['WHO Region'].unique()
        colors_map = {region: plt.cm.tab10(i) for i, region in enumerate(regions)}
        colors = [colors_map[region] for region in self.df['WHO Region']]
        
        scatter = ax.scatter(
            self.df['Confirmed'], 
            self.df['Deaths'],
            c=colors, 
            alpha=0.6, 
            s=100, 
            edgecolors='black', 
            linewidth=0.5
        )
        
        ax.set_xlabel('Confirmed Cases', fontsize=12, fontweight='bold')
        ax.set_ylabel('Deaths', fontsize=12, fontweight='bold')
        ax.set_title('COVID-19: Confirmed Cases vs Deaths', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        
        # Log scale for better visualization
        ax.set_xscale('log')
        ax.set_yscale('log')
        
        # Add legend
        legend_elements = [Patch(facecolor=colors_map[region], label=region) 
                          for region in regions]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=8)
        
        plt.tight_layout()
        display(fig, target="covid-chart3")
    
    async def generate_case_fatality_rate_chart(self):
        """
        Generate horizontal bar chart showing case fatality rates.
        
        Displays top 15 countries by CFR (filtered to countries with 1000+ cases
        for statistical significance). Displays in 'covid-chart4' element.
        """
        await asyncio.sleep(0)  # Yield control to event loop
        # Calculate CFR
        df_with_cfr = self.df.copy()
        df_with_cfr['Case Fatality Rate'] = (df_with_cfr['Deaths'] / df_with_cfr['Confirmed'] * 100)
        
        # Filter countries with at least 1000 confirmed cases for meaningful comparison
        df_filtered = df_with_cfr[df_with_cfr['Confirmed'] >= 1000]
        top_cfr = df_filtered.nlargest(15, 'Case Fatality Rate')[
            ['Country/Region', 'Case Fatality Rate', 'Deaths']
        ].sort_values('Case Fatality Rate')
        
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(top_cfr)))
        bars = ax.barh(top_cfr['Country/Region'], top_cfr['Case Fatality Rate'], color=colors)
        ax.set_xlabel('Case Fatality Rate (%)', fontsize=12, fontweight='bold')
        ax.set_title('Top 15 Countries by Case Fatality Rate\n(Countries with 1000+ confirmed cases)',
                    fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, (idx, row) in enumerate(top_cfr.iterrows()):
            ax.text(row['Case Fatality Rate'], i, f" {row['Case Fatality Rate']:.1f}%",
                   va='center', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        display(fig, target="covid-chart4")
    
    async def generate_all_charts(self):
        """
        Generate all charts concurrently (like Promise.all).
        
        Uses asyncio.gather() to run all chart generation methods
        in parallel, allowing better perceived performance.
        Can be called from JavaScript via window.generateAllCovidCharts()
        """
        await asyncio.gather(
            self.generate_top_deaths_chart(),
            self.generate_regional_deaths_pie(),
            self.generate_cases_vs_deaths_scatter(),
            self.generate_case_fatality_rate_chart()
        )
        print("✅ All visualizations generated successfully!")


# Instantiate and expose to JavaScript
from pyscript import window
from js import console

visualizer = CovidChartsVisualizer()

# Expose individual chart generation methods to window
window.generateTopDeathsChart = visualizer.generate_top_deaths_chart
window.generateRegionalDeathsPie = visualizer.generate_regional_deaths_pie
window.generateCasesVsDeathsScatter = visualizer.generate_cases_vs_deaths_scatter
window.generateCaseFatalityRateChart = visualizer.generate_case_fatality_rate_chart
window.generateAllCovidCharts = visualizer.generate_all_charts

print("✅ COVID Charts module loaded - methods exposed to window")

