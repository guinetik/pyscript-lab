"""
Data Loading Utilities for PyScript

Provides a singleton DataLoader class that caches loaded datasets to prevent
duplicate loads when multiple PyExample components request the same data.

This is particularly useful for pages with multiple visualizations that share
the same underlying dataset.

Author: Guinetik
"""

from pyodide.http import open_url
import pandas as pd
from typing import Optional, Dict
from js import console


class DataLoader:
    """
    Singleton data loader that caches DataFrames.

    When multiple PyScript examples on the same page need the same dataset,
    this class ensures the CSV is only loaded once and then reused.

    Example:
        loader = DataLoader.get_instance()
        df = loader.load_dataframe("airbnb", "/data/airbnb_listings.csv")
        # Second call returns cached data:
        df = loader.load_dataframe("airbnb", "/data/airbnb_listings.csv")
    """

    _instance: Optional['DataLoader'] = None
    _cache: Dict[str, pd.DataFrame] = {}

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(DataLoader, cls).__new__(cls)
            cls._cache = {}
            print("🗄️ DataLoader singleton created")
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'DataLoader':
        """
        Get the singleton DataLoader instance.

        Returns:
            DataLoader: The singleton instance

        Example:
            loader = DataLoader.get_instance()
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_dataframe(
        self,
        name: str,
        url: str,
        force_reload: bool = False,
        **read_csv_kwargs
    ) -> pd.DataFrame:
        """
        Load a DataFrame from a CSV file, with caching.

        If the dataset has been loaded before (identified by name), returns
        the cached version. Otherwise, loads from URL and caches it.

        Args:
            name: Identifier for this dataset (used as cache key)
            url: URL or path to the CSV file
            force_reload: If True, bypass cache and reload data
            **read_csv_kwargs: Additional arguments passed to pd.read_csv()

        Returns:
            pd.DataFrame: The loaded DataFrame

        Raises:
            ValueError: If DataFrame is empty after loading
            Exception: If CSV loading fails

        Example:
            loader = DataLoader.get_instance()

            # First call - loads from URL
            df1 = loader.load_dataframe("airbnb", "/data/airbnb.csv")

            # Second call - returns cached data
            df2 = loader.load_dataframe("airbnb", "/data/airbnb.csv")

            # Force reload
            df3 = loader.load_dataframe("airbnb", "/data/airbnb.csv", force_reload=True)
        """
        # Check cache first
        if not force_reload and name in self._cache:
            print(f"📦 Using cached data: {name} ({len(self._cache[name])} rows)")
            return self._cache[name]

        # Load fresh data
        print(f"📥 Loading data from: {url}")

        try:
            url_content = open_url(url)
            df = pd.read_csv(url_content, **read_csv_kwargs)

            if df.empty:
                raise ValueError(f"Loaded DataFrame '{name}' is empty")

            # Cache the result
            self._cache[name] = df

            print(f"✅ Loaded {name}: {len(df)} rows, {len(df.columns)} columns")
            print(f"📦 Cached as: {name}")

            return df

        except Exception as e:
            error_msg = f"Failed to load {name} from {url}: {str(e)}"
            print(f"❌ {error_msg}")
            console.error(f"❌ {error_msg}")
            raise

    def get_cached(self, name: str) -> Optional[pd.DataFrame]:
        """
        Get a cached DataFrame without attempting to load it.

        Args:
            name: Identifier of the cached dataset

        Returns:
            pd.DataFrame if cached, None otherwise

        Example:
            loader = DataLoader.get_instance()
            df = loader.get_cached("airbnb")
            if df is not None:
                print("Data is cached!")
        """
        return self._cache.get(name)

    def is_cached(self, name: str) -> bool:
        """
        Check if a dataset is cached.

        Args:
            name: Identifier of the dataset

        Returns:
            bool: True if dataset is in cache

        Example:
            loader = DataLoader.get_instance()
            if loader.is_cached("airbnb"):
                print("Airbnb data already loaded")
        """
        return name in self._cache

    def clear_cache(self, name: Optional[str] = None):
        """
        Clear cached data.

        Args:
            name: If provided, clear only this dataset. If None, clear all.

        Example:
            loader = DataLoader.get_instance()
            loader.clear_cache("airbnb")  # Clear specific dataset
            loader.clear_cache()  # Clear everything
        """
        if name is None:
            count = len(self._cache)
            self._cache.clear()
            print(f"🧹 Cleared all cached data ({count} datasets)")
        elif name in self._cache:
            del self._cache[name]
            print(f"🧹 Cleared cached data: {name}")
        else:
            print(f"⚠️ No cached data found for: {name}")

    def list_cached(self) -> list:
        """
        Get list of all cached dataset names.

        Returns:
            list: Names of cached datasets

        Example:
            loader = DataLoader.get_instance()
            cached = loader.list_cached()
            print(f"Cached datasets: {cached}")
        """
        return list(self._cache.keys())

    def load_multiple(
        self,
        name: str,
        urls: Dict[str, str],
        force_reload: bool = False,
        **read_csv_kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        Load multiple related CSVs as a single dataset.

        This is useful when a dataset consists of multiple files (e.g., nodes and edges).
        The entire collection is cached as one unit under the given name.

        Args:
            name: Identifier for this multi-file dataset
            urls: Dictionary mapping keys to URLs (e.g., {'nodes': '/data/nodes.csv', 'edges': '/data/edges.csv'})
            force_reload: If True, bypass cache and reload all files
            **read_csv_kwargs: Additional arguments passed to pd.read_csv()

        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping keys to loaded DataFrames

        Example:
            loader = DataLoader.get_instance()
            data = loader.load_multiple(
                "stackoverflow_network",
                {
                    'nodes': '/data/stack_network_nodes.csv',
                    'edges': '/data/stack_network_links.csv'
                }
            )
            nodes_df = data['nodes']
            edges_df = data['edges']
        """
        # Check cache first
        if not force_reload and name in self._cache:
            print(f"📦 Using cached dataset: {name}")
            return self._cache[name]

        # Load all files
        print(f"📥 Loading multi-file dataset: {name}")
        result = {}

        try:
            for key, url in urls.items():
                print(f"📥  Loading {key} from: {url}")
                url_content = open_url(url)
                df = pd.read_csv(url_content, **read_csv_kwargs)

                if df.empty:
                    raise ValueError(f"Loaded DataFrame '{key}' is empty")

                result[key] = df
                print(f"✅  {key}: {len(df)} rows, {len(df.columns)} columns")

            # Cache the entire collection
            self._cache[name] = result
            print(f"📦 Cached as: {name}")

            return result

        except Exception as e:
            error_msg = f"Failed to load {name}: {str(e)}"
            print(f"❌ {error_msg}")
            console.error(f"❌ {error_msg}")
            raise


# Convenience functions for quick access
def load_csv(name: str, url: str, **kwargs) -> pd.DataFrame:
    """
    Convenience function to load CSV with caching.

    Args:
        name: Dataset identifier
        url: CSV file URL
        **kwargs: Additional pd.read_csv arguments

    Returns:
        pd.DataFrame: The loaded DataFrame

    Example:
        from lib.data import load_csv
        df = load_csv("airbnb", "/data/airbnb.csv")
    """
    loader = DataLoader.get_instance()
    return loader.load_dataframe(name, url, **kwargs)


def load_network_data(
    name: str,
    nodes_url: str = "/data/stack_network_nodes.csv",
    edges_url: str = "/data/stack_network_links.csv",
    **kwargs
) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to load network graph data (nodes + edges).

    Args:
        name: Dataset identifier
        nodes_url: Path to nodes CSV
        edges_url: Path to edges CSV
        **kwargs: Additional pd.read_csv arguments

    Returns:
        Dict with 'nodes' and 'edges' DataFrames

    Example:
        from lib.data import load_network_data
        data = load_network_data("stackoverflow")
        nodes_df = data['nodes']
        edges_df = data['edges']
    """
    loader = DataLoader.get_instance()
    return loader.load_multiple(
        name,
        {'nodes': nodes_url, 'edges': edges_url},
        **kwargs
    )
