import pandas as pd
import os

# Get the directory of this file (core/) and then its parent (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The dataset is located in the 'Data' folder (capital D)
DATA_DIR = os.path.join(BASE_DIR, "Data")

def load_macro() -> pd.DataFrame:
    """Loads macroeconomics time series data (2020-2025)."""
    path = os.path.join(DATA_DIR, "vietnam_macro_2020_2025.csv")
    return pd.read_csv(path)

def load_regions() -> pd.DataFrame:
    """Loads regional statistics data (2024, 6 regions)."""
    path = os.path.join(DATA_DIR, "vietnam_regions_2024.csv")
    return pd.read_csv(path)

def load_sectors() -> pd.DataFrame:
    """Loads sectoral statistics data (2024, 10 sectors)."""
    path = os.path.join(DATA_DIR, "vietnam_sectors_2024.csv")
    return pd.read_csv(path)
