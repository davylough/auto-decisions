
"""Application entry point."""
from pathlib import Path
import pandas as pd


def run_package():
    print("yeet1")
    df = pd.read_csv('data/01_raw/small.csv')
    print(df.to_string()) 
    return "yeet"


if __name__ == "__main__":
    run_package()
