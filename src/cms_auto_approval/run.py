
"""Application entry point."""
from pathlib import Path
import pandas as pd


def run_package():
    print("yeet1")
    df = pd.read_csv('data/01_raw/small.csv')
    return df.head()


if __name__ == "__main__":
    run_package()
